#!/usr/bin/env python3
"""Check Cloudflare blocked IPs from IDS"""

import requests
import os

api_key = os.getenv('CLOUDFLARE_API_KEY')
zone_id = os.getenv('CLOUDFLARE_ZONE_ID')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

response = requests.get(
    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules',
    headers=headers
)

data = response.json()
if data['success']:
    print('CLOUDFLARE BLOCKED IPs (by IDS):')
    print('=' * 100)
    ids_rules = [r for r in data['result'] if 'Python IDS' in r.get('notes', '')]
    
    for rule in ids_rules:
        ip = rule['configuration']['value']
        mode = rule['mode']
        rule_id = rule['id']
        print(f'IP: {ip:18} | Mode: {mode:6} | Rule ID: {rule_id}')
    
    print()
    print(f'Total IDS rules in Cloudflare: {len(ids_rules)}')
else:
    print('Error:', data.get('errors'))
