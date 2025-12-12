import re
import time
import sqlite3
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os
import logging
from geoip_checker import geoip


class IntrusionDetector:
    def __init__(self, log_path, config_path="config.json"):
        self.log_path = log_path
        self.logger = logging.getLogger(__name__)

        self.suspicious_patterns = [
            # Common vulnerability probes
            r"(\.\./)+",  # Directory traversal
            r"/(wp-admin|wp-login|phpmyadmin|adminer)",  # Admin panels
            r"\.(php|asp|aspx|jsp|pl)\b",  # Script files
            r"\b(union|select|insert|update|delete|drop|exec)\b",  # SQLi
            r"<script>|javascript:",  # XSS attempts
            r"/\.env|/\.git|/\.htaccess",  # Sensitive files
            r"\b(eval|system|shell_exec|passthru)\b",  # Code execution
            r"\?.*=.*(http|ftp|file):",  # SSRF/LFI patterns
            r"\.\.%2f|%2e%2e%2f",  # URL-encoded traversal
        ]

        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.suspicious_patterns
        ]

        # Load config
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "threshold": 10,  # Requests per minute to trigger blocking
                "block_duration": 3600,  # Block for 1 hour
                "whitelist": ["127.0.0.1", "::1"],
                "log_types": ["access", "error"],
                "alert_email": None,
                "cloudflare_enabled": True,
                "cloudflare_api_key": os.getenv("CLOUDFLARE_API_KEY"),
                "cloudflare_zone_id": os.getenv("CLOUDFLARE_ZONE_ID"),
            }

        # Initialize database
        self.init_database()

    def init_database(self):
        # Don't initialize connection here - will be created per-thread
        pass

    def get_db_connection(self):
        """Get a fresh database connection (thread-safe)"""
        conn = sqlite3.connect("intrusion_data.db")
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS suspicious_ips (
                ip TEXT PRIMARY KEY,
                count INTEGER,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                is_blocked BOOLEAN DEFAULT 0,
                block_until TIMESTAMP,
                cloudflare_rule_id TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attack_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                ip TEXT,
                url TEXT,
                user_agent TEXT,
                attack_type TEXT,
                severity INTEGER
            )
        """
        )

        conn.commit()
        return conn

    def analyze_log_line(self, line):
        """Parse and analyze a single log line"""
        # Common log formats (adjust for your web server)
        # Apache: 127.0.0.1 - - [10/Dec/2024:10:10:10] "GET /wp-admin HTTP/1.1" 404
        # Nginx: 127.0.0.1 - - [10/Dec/2024:10:10:10] "GET /test.php" 200
        # IIS: 2024-12-10 10:10:10 127.0.0.1 GET /wp-admin - 404

        # ReDoS-safe regex: simple digit pattern with bounded context, no backtracking
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        if not ip_match:
            return None

        ip = ip_match.group(1)

        # Check if IP is whitelisted
        if self.is_whitelisted(ip):
            return None

        # Extract URL
        url_match = re.search(r'"(GET|POST|PUT|DELETE|HEAD)\s+([^\s]+)', line)
        url = url_match.group(2) if url_match else ""

        # Extract User-Agent
        ua_match = re.search(r'"([^"]*)"\s*$', line)
        user_agent = ua_match.group(1) if ua_match else ""

        # INSTANT BLOCK: If IP is from Russia or China, block immediately (no threshold)
        if geoip.is_blocked_country(ip):
            country = geoip.get_country(ip)
            severity = 10  # Maximum severity
            attack_type = f"{country} IP - Geographic Block"
            self.log_attack(ip, url, user_agent, attack_type, severity)

            # Check if already blocked
            cursor = self.get_db_connection().cursor()
            cursor.execute("SELECT is_blocked FROM suspicious_ips WHERE ip = ?", (ip,))
            result = cursor.fetchone()

            if not result or not result[0]:
                # Block immediately
                self.block_ip(ip)

            return {
                "ip": ip,
                "url": url,
                "attack_type": attack_type,
                "severity": severity,
                "timestamp": datetime.now(),
                "auto_blocked": True,
            }

        # Check for suspicious patterns
        attack_type = self.detect_attack(url, user_agent, line)

        if attack_type:
            severity = self.assess_severity(attack_type)
            self.log_attack(ip, url, user_agent, attack_type, severity)
            self.update_ip_stats(ip)
            return {
                "ip": ip,
                "url": url,
                "attack_type": attack_type,
                "severity": severity,
                "timestamp": datetime.now(),
            }

        return None

    def detect_attack(self, url, user_agent, line):
        """Detect type of attack"""
        test_string = f"{url} {user_agent} {line}".lower()

        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(test_string):
                attack_types = [
                    "Directory Traversal",
                    "Admin Panel Probe",
                    "Script File Access",
                    "SQL Injection",
                    "XSS Attempt",
                    "Sensitive File Access",
                    "Code Execution Attempt",
                    "SSRF/LFI",
                    "Encoded Traversal",
                ]
                return attack_types[i % len(attack_types)]

        # Check for excessive requests
        if self.is_excessive_request(line):
            return "Brute Force Attempt"

        return None

    def assess_severity(self, attack_type):
        """Assign severity level (1-10)"""
        severity_map = {
            "SQL Injection": 9,
            "Code Execution Attempt": 10,
            "Directory Traversal": 8,
            "XSS Attempt": 7,
            "SSRF/LFI": 8,
            "Admin Panel Probe": 6,
            "Script File Access": 5,
            "Sensitive File Access": 6,
            "Encoded Traversal": 7,
            "Brute Force Attempt": 6,
        }
        return severity_map.get(attack_type, 5)

    def update_ip_stats(self, ip):
        """Update IP statistics in database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        now = datetime.now()

        cursor.execute(
            """
            INSERT OR REPLACE INTO suspicious_ips 
            (ip, count, first_seen, last_seen)
            VALUES (?, 
                COALESCE((SELECT count FROM suspicious_ips WHERE ip = ?), 0) + 1,
                COALESCE((SELECT first_seen FROM suspicious_ips WHERE ip = ?), ?),
                ?)
        """,
            (ip, ip, ip, now, now),
        )

        conn.commit()

        # Check if IP should be blocked
        cursor.execute("SELECT count FROM suspicious_ips WHERE ip = ?", (ip,))
        result = cursor.fetchone()
        if result and result[0] > self.config["threshold"]:
            self.block_ip(ip)

        conn.close()

    def block_ip(self, ip):
        """Block the IP address"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        block_until = datetime.now() + timedelta(seconds=self.config["block_duration"])

        cursor.execute(
            """
            UPDATE suspicious_ips 
            SET is_blocked = 1, block_until = ?
            WHERE ip = ?
        """,
            (block_until, ip),
        )

        conn.commit()
        conn.close()

        # Execute blocking actions (Cloudflare only on Windows)
        self.execute_block(ip)

        self.logger.info(f"[BLOCKED] IP {ip} blocked until {block_until}")

    def execute_block(self, ip):
        """Execute actual blocking via Cloudflare"""
        # Windows doesn't have iptables or .htaccess - use Cloudflare only
        self.block_cloudflare(ip)

    def block_cloudflare(self, ip):
        """Block IP via Cloudflare API"""
        api_key = self.config.get("cloudflare_api_key") or os.getenv(
            "CLOUDFLARE_API_KEY"
        )
        zone_id = self.config.get("cloudflare_zone_id") or os.getenv(
            "CLOUDFLARE_ZONE_ID"
        )

        if not api_key or not zone_id:
            self.logger.warning(
                f"[CLOUDFLARE] Missing API credentials, cannot block {ip}"
            )
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "mode": "block",
            "configuration": {"target": "ip", "value": ip},
            "notes": f"Blocked by Python IDS - {datetime.now()}",
        }

        try:
            response = requests.post(
                f"https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules",
                headers=headers,
                json=data,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                rule_id = response.json().get("result", {}).get("id")
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    UPDATE suspicious_ips 
                    SET cloudflare_rule_id = ?
                    WHERE ip = ?
                """,
                    (rule_id, ip),
                )
                self.conn.commit()
                self.logger.info(
                    f"[CLOUDFLARE] IP {ip} blocked successfully (Rule ID: {rule_id})"
                )
            else:
                self.logger.error(
                    f"[CLOUDFLARE] Failed to block {ip}: {response.status_code} - {response.text}"
                )
        except Exception as e:
            self.logger.error(f"[ERROR] Cloudflare blocking failed for {ip}: {e}")

    def unblock_ip(self, ip):
        """Unblock an IP address"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cloudflare_rule_id FROM suspicious_ips WHERE ip = ?", (ip,)
        )
        result = cursor.fetchone()

        if result and result[0]:
            rule_id = result[0]
            self.unblock_cloudflare(ip, rule_id)

        cursor.execute(
            """
            UPDATE suspicious_ips 
            SET is_blocked = 0, block_until = NULL
            WHERE ip = ?
        """,
            (ip,),
        )

        conn.commit()
        conn.close()
        self.logger.info(f"[UNBLOCKED] IP {ip} unblocked")

    def unblock_cloudflare(self, ip, rule_id):
        """Remove IP block from Cloudflare"""
        api_key = self.config.get("cloudflare_api_key") or os.getenv(
            "CLOUDFLARE_API_KEY"
        )
        zone_id = self.config.get("cloudflare_zone_id") or os.getenv(
            "CLOUDFLARE_ZONE_ID"
        )

        if not api_key or not zone_id:
            self.logger.warning(
                f"[CLOUDFLARE] Missing API credentials, cannot unblock {ip}"
            )
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.delete(
                f"https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules/{rule_id}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                self.logger.info(f"[CLOUDFLARE] IP {ip} unblocked successfully")
            else:
                self.logger.error(
                    f"[CLOUDFLARE] Failed to unblock {ip}: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"[ERROR] Cloudflare unblocking failed for {ip}: {e}")

    def is_whitelisted(self, ip):
        """Check if IP is in whitelist"""
        for whitelist_ip in self.config.get("whitelist", []):
            if ip == whitelist_ip:
                return True
        return False

    def is_excessive_request(self, line):
        """Detect excessive requests (simple rate limiting)"""
        ip_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
        if ip_match:
            ip = ip_match.group(1)
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM attack_logs 
                WHERE ip = ? AND timestamp > datetime('now', '-1 minute')
            """,
                (ip,),
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count > 30  # More than 30 requests per minute
        return False

    def log_attack(self, ip, url, user_agent, attack_type, severity):
        """Log attack details to database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attack_logs (timestamp, ip, url, user_agent, attack_type, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (datetime.now(), ip, url, user_agent, attack_type, severity),
        )
        conn.commit()
        conn.close()

    def check_block_expiry(self):
        """Check and unblock expired IP blocks"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        now = datetime.now()

        cursor.execute(
            """
            SELECT ip FROM suspicious_ips 
            WHERE is_blocked = 1 AND block_until < ?
        """,
            (now,),
        )

        expired_ips = cursor.fetchall()
        conn.close()

        for (ip,) in expired_ips:
            self.unblock_ip(ip)

    def monitor_logs(self):
        """Continuously monitor log files"""
        self.logger.info(f"[INFO] Starting intrusion detection on {self.log_path}")

        # Get current file size
        if not os.path.exists(self.log_path):
            self.logger.error(f"[ERROR] Log file not found: {self.log_path}")
            return

        with open(self.log_path, "r") as f:
            f.seek(0, 2)  # Seek to end
            last_size = f.tell()

        check_expiry_counter = 0

        while True:
            try:
                with open(self.log_path, "r") as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    last_size = f.tell()

                for line in new_lines:
                    result = self.analyze_log_line(line)
                    if result:
                        self.logger.warning(
                            f"[ALERT] {result['attack_type']} from {result['ip']} - {result['url']}"
                        )

                # Check for expired blocks every 60 iterations (roughly every 5 minutes)
                check_expiry_counter += 1
                if check_expiry_counter >= 60:
                    self.check_block_expiry()
                    check_expiry_counter = 0

                time.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                self.logger.info("\n[INFO] Stopping intrusion detection")
                break
            except Exception as e:
                self.logger.error(f"[ERROR] {e}")
                time.sleep(10)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("intrusion_detector.log"),
            logging.StreamHandler(),
        ],
    )

    # Example usage - modify log_path to your actual Windows log file
    # For IIS: typically in C:\inetpub\logs\LogFiles\
    # For Nginx on Windows: wherever you configured the access log
    detector = IntrusionDetector(log_path="C:\\logs\\access.log")
    detector.monitor_logs()
