#!/usr/bin/env python3
"""
Block all Chinese and Russian IP address ranges in Cloudflare
Uses the MaxMind GeoIP2 database or manual IP ranges
"""

import requests
import os
import json
import sys
from datetime import datetime

# Force UTF-8 output
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def get_china_ranges():
    """Get China IP ranges."""
    return [
        "1.0.0.0/24",  # China Telecom
        "27.0.0.0/8",  # China Telecom/Netcom
        "36.0.0.0/7",  # China Netcom
        "42.0.0.0/8",  # China Telecom
        "58.0.0.0/7",  # China Netcom
        "60.0.0.0/8",  # China Telecom
        "61.0.0.0/8",  # China Telecom
        "110.0.0.0/8",  # China Netcom
        "111.0.0.0/8",  # China Telecom
        "112.0.0.0/8",  # China Telecom
        "113.0.0.0/8",  # China Unicom
        "114.0.0.0/8",  # China Telecom
        "115.0.0.0/8",  # China Telecom
        "116.0.0.0/8",  # China Unicom
        "117.0.0.0/8",  # China Telecom
        "118.0.0.0/8",  # China Telecom
        "119.0.0.0/8",  # China Telecom
        "120.0.0.0/8",  # China Telecom
        "121.0.0.0/8",  # China Telecom
        "122.0.0.0/8",  # China Netcom
        "123.0.0.0/8",  # China Telecom
        "124.0.0.0/8",  # China Telecom
        "125.0.0.0/8",  # China Netcom
        "126.0.0.0/8",  # China Netcom
        "175.0.0.0/8",  # China Telecom
        "180.0.0.0/8",  # China Telecom
        "182.0.0.0/8",  # China Unicom
        "183.0.0.0/8",  # China Telecom
        "202.0.0.0/8",  # China Telecom
        "203.0.0.0/8",  # China Telecom
        "210.0.0.0/8",  # China Telecom
        "211.0.0.0/8",  # China Netcom
        "218.0.0.0/8",  # China Telecom
        "219.0.0.0/8",  # China Netcom
        "220.0.0.0/8",  # China Telecom
        "221.0.0.0/8",  # China Telecom
        "222.0.0.0/8",  # China Telecom
        "223.0.0.0/8",  # China Telecom
    ]


def get_russia_ranges():
    """Get Russia IP ranges."""
    return [
        "5.0.0.0/8",  # Russian Federation
        "31.0.0.0/8",  # Russian Federation
        "37.0.0.0/8",  # Russian Federation
        "46.0.0.0/8",  # Russian Federation
        "77.0.0.0/8",  # Russian Federation
        "79.0.0.0/8",  # Russian Federation
        "80.0.0.0/8",  # Russian Federation
        "83.0.0.0/8",  # Russian Federation
        "85.0.0.0/8",  # Russian Federation
        "86.0.0.0/8",  # Russian Federation
        "87.0.0.0/8",  # Russian Federation
        "88.0.0.0/8",  # Russian Federation
        "89.0.0.0/8",  # Russian Federation
        "91.0.0.0/8",  # Russian Federation
        "92.0.0.0/8",  # Russian Federation
        "93.0.0.0/8",  # Russian Federation
        "94.0.0.0/8",  # Russian Federation
        "95.0.0.0/8",  # Russian Federation
        "109.0.0.0/8",  # Russian Federation
        "149.0.0.0/8",  # Russian Federation
        "185.0.0.0/8",  # Russian Federation
        "188.0.0.0/8",  # Russian Federation
        "195.0.0.0/8",  # Russian Federation
        "212.0.0.0/8",  # Russian Federation
        "213.0.0.0/8",  # Russian Federation
        "217.0.0.0/8",  # Russian Federation
    ]


# Major Chinese and Russian IP CIDR blocks (not exhaustive, but covers major ranges)
BLOCKED_RANGES = {"China": get_china_ranges(), "Russia": get_russia_ranges()}


def block_ip_range(api_key, zone_id, ip_range, country):
    """Block a single IP range in Cloudflare"""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    data = {
        "mode": "block",
        "configuration": {"target": "ip_range", "value": ip_range},
        "notes": f"Blocked {country} IP range - {ip_range} - Batch block by Python IDS - {datetime.now()}",
    }

    try:
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules",
            headers=headers,
            json=data,
            timeout=10,
        )

        if response.status_code in [200, 201]:
            result = response.json()
            if result.get("success"):
                rule_id = result.get("result", {}).get("id")
                return True, rule_id
            else:
                errors = result.get("errors", [])
                error_msg = errors[0].get("message") if errors else "Unknown error"
                return False, error_msg
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


def process_country_ranges(api_key, zone_id, country, ranges):
    """Process IP ranges for a specific country"""
    blocked_count = 0
    failed_count = 0
    duplicates = 0

    print(f"\n{'=' * 100}")
    print(f"Blocking {country} IP Ranges ({len(ranges)} ranges)")
    print(f"{'=' * 100}")

    for i, ip_range in enumerate(ranges, 1):
        success, result = block_ip_range(api_key, zone_id, ip_range, country)

        if success:
            print(
                f"[OK] [{i:3}/{len(ranges)}] {ip_range:20} -> Blocked (Rule: {result[:16]}...)"
            )
            blocked_count += 1
        elif "duplicate_of_existing" in str(result):
            print(
                f"[DUP] [{i:3}/{len(ranges)}] {ip_range:20} -> Already blocked (duplicate)"
            )
            duplicates += 1
        else:
            print(f"[FAIL] [{i:3}/{len(ranges)}] {ip_range:20} -> Failed: {result}")
            failed_count += 1

    return blocked_count, failed_count, duplicates


def main():
    """Block all Chinese and Russian IP ranges"""
    api_key = os.getenv("CLOUDFLARE_API_KEY")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")

    if not api_key or not zone_id:
        print("Error: CLOUDFLARE_API_KEY or CLOUDFLARE_ZONE_ID not set")
        return 1

    print("=" * 100)
    print("Blocking Chinese and Russian IP Ranges")
    print("=" * 100)
    print()

    total_ranges = sum(len(ranges) for ranges in BLOCKED_RANGES.values())
    print(f"Total IP ranges to block: {total_ranges}")
    print()

    blocked_count = 0
    failed_count = 0
    duplicates = 0

    for country, ranges in BLOCKED_RANGES.items():
        cnt_blk, cnt_fail, cnt_dup = process_country_ranges(
            api_key, zone_id, country, ranges
        )
        blocked_count += cnt_blk
        failed_count += cnt_fail
        duplicates += cnt_dup

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Successfully blocked: {blocked_count}")
    print(f"Already blocked (duplicates): {duplicates}")
    print(f"Failed: {failed_count}")
    print(f"Total processed: {blocked_count + duplicates + failed_count}")
    print()

    if failed_count == 0:
        print("[OK] All IP ranges processed successfully!")
        return 0
    else:
        print(f"[FAIL] {failed_count} ranges failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
