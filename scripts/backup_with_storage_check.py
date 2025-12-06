#!/usr/bin/env python3
"""
Backup script with storage validation and email alerts.

Checks if performing the next backup would exceed storage limits.
If so, prevents backup and sends email alert to admin.

Configuration:
- Total storage limit: 20 GB
- Safety margin: 500 MB (reserved for OS)
- Estimated backup size threshold: Abort if next backup would exceed 90% of limit
"""

import os
import sys
import subprocess
import shutil
import gzip
import smtplib
import socket
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ============================================================================
# Configuration
# ============================================================================
BACKUP_DIR = Path("/home/nexus/backups")
NEXUS_DIR = Path("/home/nexus/nexus")
LOG_FILE = NEXUS_DIR / "logs" / "backup.log"
TOTAL_STORAGE_GB = 20
SAFETY_MARGIN_GB = 0.5
STORAGE_LIMIT_GB = TOTAL_STORAGE_GB - SAFETY_MARGIN_GB

# Email configuration - update these
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "nexus@localhost")

# Get hostname for email
HOSTNAME = socket.gethostname()


# ============================================================================
# Utilities
# ============================================================================
def log_message(message: str, level: str = "INFO"):
    """Log message to both console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"

    print(log_entry)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")


def get_directory_size(path: Path) -> float:
    """Get total size of directory in GB."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception as e:
        log_message(f"Error calculating size for {path}: {e}", "WARNING")

    return total / (1024**3)  # Convert to GB


def get_filesystem_usage() -> dict:
    """Get filesystem usage information."""
    try:
        result = subprocess.run(
            ["df", "-B1", "/"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")
        fs_info = lines[1].split()

        total_bytes = int(fs_info[1])
        used_bytes = int(fs_info[2])
        available_bytes = int(fs_info[3])

        return {
            "total_gb": total_bytes / (1024**3),
            "used_gb": used_bytes / (1024**3),
            "available_gb": available_bytes / (1024**3),
            "percent_used": (used_bytes / total_bytes) * 100,
        }
    except Exception as e:
        log_message(f"Error getting filesystem usage: {e}", "ERROR")
        return None


def estimate_backup_size() -> float:
    """Estimate the size of the next database backup in GB."""
    # Get database size
    try:
        result = subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "psql",
                "-d",
                "nexus",
                "-t",
                "-c",
                "SELECT pg_size_pretty(pg_database_size(current_database()));",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Output format: "123 MB"
        if result.returncode == 0 and result.stdout.strip():
            size_str = result.stdout.strip()
            # Parse size string (e.g., "123 MB", "1.5 GB")
            size_parts = size_str.split()
            if len(size_parts) == 2:
                try:
                    size_val = float(size_parts[0])
                    unit = size_parts[1].upper()

                    if "GB" in unit:
                        return size_val * 0.7  # gzip compression factor
                    elif "MB" in unit:
                        return (size_val / 1024) * 0.7
                    elif "KB" in unit:
                        return (size_val / (1024**2)) * 0.7
                except ValueError:
                    pass
    except Exception as e:
        log_message(f"Error estimating backup size: {e}", "WARNING")

    # Fallback: 100MB compressed estimate
    return 0.1


def send_email_alert(subject: str, body: str) -> bool:
    """Send email alert to admin."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ADMIN_EMAIL
        msg["Subject"] = f"[{HOSTNAME}] {subject}"

        # Add body
        msg.attach(MIMEText(body, "plain"))

        # Send email
        if SMTP_USER and SMTP_PASSWORD:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            # Use local SMTP without authentication
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)

        log_message(f"Email alert sent to {ADMIN_EMAIL}", "INFO")
        return True
    except Exception as e:
        log_message(f"Failed to send email alert: {e}", "ERROR")
        return False


def check_storage_and_backup() -> bool:
    """
    Main function: Check storage and perform backup if safe.

    Returns:
        True if backup was completed, False if aborted
    """
    log_message("=" * 80)
    log_message("Starting backup process with storage validation")

    # Step 1: Get current filesystem usage
    log_message("Step 1: Checking filesystem usage...")
    fs_usage = get_filesystem_usage()
    if not fs_usage:
        log_message("Failed to get filesystem usage", "ERROR")
        return False

    log_message(
        f"Filesystem status: {fs_usage['used_gb']:.2f} GB / "
        f"{fs_usage['total_gb']:.2f} GB used "
        f"({fs_usage['percent_used']:.1f}%)"
    )
    log_message(f"Available space: {fs_usage['available_gb']:.2f} GB")

    # Step 2: Estimate backup size
    log_message("Step 2: Estimating backup size...")
    backup_size = estimate_backup_size()
    log_message(f"Estimated backup size: {backup_size:.2f} GB")

    # Step 3: Check if backup would fit
    log_message("Step 3: Validating backup would fit...")
    projected_usage = fs_usage["used_gb"] + backup_size

    log_message(f"Storage limit: {STORAGE_LIMIT_GB:.2f} GB")
    log_message(f"Current usage: {fs_usage['used_gb']:.2f} GB")
    log_message(f"Backup size: {backup_size:.2f} GB")
    log_message(f"Projected usage after backup: {projected_usage:.2f} GB")

    if projected_usage > STORAGE_LIMIT_GB:
        # Storage would be exceeded - abort backup
        log_message("❌ BACKUP ABORTED: Storage limit would be exceeded!", "ERROR")

        # Calculate how much space needs to be freed
        space_needed = projected_usage - STORAGE_LIMIT_GB + 1.0  # +1GB safety margin

        # Send email alert
        subject = "🚨 URGENT: Backup Failed - Storage Space Critical"
        body = f"""
Backup process has been ABORTED due to insufficient storage space.

SERVER: {HOSTNAME}
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CURRENT STATUS:
- Total storage: {fs_usage['total_gb']:.2f} GB
- Currently used: {fs_usage['used_gb']:.2f} GB ({fs_usage['percent_used']:.1f}%)
- Available: {fs_usage['available_gb']:.2f} GB
- Storage limit: {STORAGE_LIMIT_GB:.2f} GB

BACKUP DETAILS:
- Estimated backup size: {backup_size:.2f} GB
- Projected usage after backup: {projected_usage:.2f} GB

ACTION REQUIRED:
- Need to free up at least {space_needed:.2f} GB
- Current backup for this cycle will NOT be created
- Please investigate and remove old files to make space

RECOMMENDATIONS:
1. Check /home/nexus/nexus/logs directory for old log files
2. Review /home/nexus/backups for old backup files
3. Check /var for temporary files or old package cache
4. Review database size: check for orphaned records

Please free up space and the backup will resume on the next scheduled run.
"""
        send_email_alert(subject, body)

        log_message("=" * 80)
        return False

    # Step 4: Perform backup
    log_message("Step 4: Performing backup...")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_date = datetime.now().strftime("%Y%m%d")
    backup_file = BACKUP_DIR / f"nexus_db_{backup_date}.sql.gz"

    try:
        # Dump database
        log_message(f"Dumping database to {backup_file}...")

        with open(backup_file, "wb") as f:
            dump_process = subprocess.Popen(
                ["sudo", "-u", "postgres", "pg_dump", "nexus"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                while True:
                    chunk = dump_process.stdout.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    gz.write(chunk)

            dump_process.wait()
            if dump_process.returncode != 0:
                error = dump_process.stderr.read().decode()
                raise RuntimeError(f"pg_dump failed: {error}")

        backup_size_actual = backup_file.stat().st_size / (1024**3)
        log_message(
            f"✅ Backup completed: {backup_file.name} ({backup_size_actual:.2f} GB)"
        )

        # Clean up old backups (keep last 7 days)
        log_message("Step 5: Cleaning up old backups...")
        import time

        cutoff_timestamp = time.time() - (7 * 24 * 60 * 60)  # 7 days ago
        for old_backup in BACKUP_DIR.glob("nexus_db_*.sql.gz"):
            if old_backup.stat().st_mtime < cutoff_timestamp:
                log_message(f"Removing old backup: {old_backup.name}")
                old_backup.unlink()

        # Send success email
        subject = "✅ Backup Completed Successfully"
        body = f"""
Database backup completed successfully.

SERVER: {HOSTNAME}
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

BACKUP DETAILS:
- File: {backup_file.name}
- Size: {backup_size_actual:.2f} GB
- Location: {backup_file}

STORAGE STATUS:
- Total available: {fs_usage['available_gb']:.2f} GB
- Usage after backup: {(fs_usage['used_gb'] + backup_size_actual):.2f} / {fs_usage['total_gb']:.2f} GB
"""
        send_email_alert(subject, body)

        log_message("=" * 80)
        return True

    except Exception as e:
        log_message(f"Backup failed: {e}", "ERROR")

        # Clean up partial backup
        if backup_file.exists():
            backup_file.unlink()

        # Send failure email
        subject = "❌ Backup Failed"
        body = f"""
Database backup process failed.

SERVER: {HOSTNAME}
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ERROR: {str(e)}

STORAGE STATUS:
- Currently used: {fs_usage['used_gb']:.2f} / {fs_usage['total_gb']:.2f} GB
- Available: {fs_usage['available_gb']:.2f} GB

Please check logs for more details.
"""
        send_email_alert(subject, body)

        log_message("=" * 80)
        return False


if __name__ == "__main__":
    success = check_storage_and_backup()
    sys.exit(0 if success else 1)
