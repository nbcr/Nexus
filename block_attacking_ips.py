#!/usr/bin/env python3
"""
Block Chinese and Russian IPs detected from attack logs
More practical: blocks actual attacking IPs instead of entire ranges
"""

import sqlite3
import requests
import os
import sys
from datetime import datetime
from collections import defaultdict

# Force UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def get_attacking_ips():
    """Get all attacking IPs from intrusion database"""
    conn = sqlite3.connect('intrusion_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT ip FROM attack_logs ORDER BY ip')
    ips = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return ips

def block_ip_individual(api_key, zone_id, ip):
    """Block a single IP in Cloudflare"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'mode': 'block',
        'configuration': {'target': 'ip', 'value': ip},
        'notes': f'Blocked by Python IDS - Attacking IP - {datetime.now()}'
    }
    
    try:
        response = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            if result.get('success'):
                rule_id = result.get('result', {}).get('id')
                return True, rule_id
            else:
                errors = result.get('errors', [])
                error_msg = errors[0].get('message') if errors else 'Unknown error'
                return False, error_msg
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """Block all attacking IPs from intrusion database"""
    api_key = os.getenv('CLOUDFLARE_API_KEY')
    zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
    
    if not api_key or not zone_id:
        print("[ERROR] CLOUDFLARE_API_KEY or CLOUDFLARE_ZONE_ID not set")
        return 1
    
    # Get attacking IPs
    attacking_ips = get_attacking_ips()
    
    if not attacking_ips:
        print("[INFO] No attacking IPs found in database. Run tests first.")
        return 0
    
    print("=" * 100)
    print("Blocking All Detected Attacking IPs")
    print("=" * 100)
    print()
    print(f"Found {len(attacking_ips)} unique attacking IPs to block")
    print()
    
    blocked_count = 0
    failed_count = 0
    duplicates = 0
    
    for i, ip in enumerate(attacking_ips, 1):
        success, result = block_ip_individual(api_key, zone_id, ip)
        
        if success:
            print(f"[OK] [{i:3}/{len(attacking_ips)}] {ip:18} -> Blocked")
            blocked_count += 1
        else:
            if 'duplicate_of_existing' in str(result):
                print(f"[DUP] [{i:3}/{len(attacking_ips)}] {ip:18} -> Already blocked")
                duplicates += 1
            else:
                print(f"[FAIL] [{i:3}/{len(attacking_ips)}] {ip:18} -> Error: {result}")
                failed_count += 1
    
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
        print("[OK] All attacking IPs blocked!")
        return 0
    else:
        print(f"[WARN] {failed_count} IPs had errors. Already blocked IPs are normal.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
