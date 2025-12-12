#!/usr/bin/env python3
"""
Test script to simulate malicious requests from Russian IPs
This will add fake log entries to test the IDS blocking functionality
"""

import os
from datetime import datetime, timedelta
import random


def create_test_log_entries():
    """Create test log entries simulating attacks from Russian IPs"""

    # Russian IP ranges (real ranges for testing purposes)
    russian_ips = [
        "185.220.100.45",  # Russian VPS provider
        "89.163.128.100",  # Russian ISP
        "195.154.200.75",  # Russian datacenter
    ]

    # Attack patterns to simulate
    attack_patterns = [
        "GET /../../../etc/passwd HTTP/1.1",  # Directory traversal
        "GET /wp-admin HTTP/1.1",  # Admin panel probe
        "GET /test.php HTTP/1.1",  # Script file access
        "GET /admin.aspx HTTP/1.1",  # Admin access attempt
        "GET /.env HTTP/1.1",  # Environment file access
        "GET /config.php HTTP/1.1",  # Config file access
    ]

    user_agents = [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "curl/7.64.1",
        "Wget/1.20.3",
        "python-requests/2.25.1",
    ]

    log_file = "C:\\Nexus\\logs\\access.log"

    print(f"Adding test attack logs to {log_file}")
    print(f"Russian IPs to test: {', '.join(russian_ips)}")
    print()

    # Append test entries to the access log
    try:
        with open(log_file, "a") as f:
            for ip in russian_ips:
                # Create multiple attack attempts from each IP (to exceed threshold of 10)
                for _ in range(15):
                    timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
                    attack = random.choice(attack_patterns)
                    user_agent = random.choice(user_agents)
                    status = (
                        "404" if "wp-admin" in attack or ".php" in attack else "403"
                    )

                    # Apache/Nginx combined log format
                    log_line = f'{ip} - - [{timestamp}] "{attack}" {status} 0 "-" "{user_agent}"\n'
                    f.write(log_line)

                    print(f"✓ Added: {ip} -> {attack[:50]}")

        print()
        print(f"✓ Added {len(russian_ips) * 15} test log entries")
        print()
        print("IDS should now:")
        print("  1. Detect these attacks from Russian IPs")
        print("  2. Block each IP after 10+ suspicious requests")
        print("  3. Create Cloudflare rules")
        print()
        print("Check intrusion_detector.log for details")
        print("Check Cloudflare dashboard IP Access Rules to see blocks")

    except FileNotFoundError:
        print(f"Error: Log file not found: {log_file}")
        print("Make sure the server is running and has created the log file")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    create_test_log_entries()
