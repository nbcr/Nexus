#!/usr/bin/env python3
"""Test instant blocking of Russia/China IPs"""

from datetime import datetime

# Add test entries from a new Russian IP
log_file = 'C:\\Nexus\\logs\\access.log'
new_russian_ip = '212.100.200.1'  # Russian IP range

with open(log_file, 'a') as f:
    timestamp = datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0000')
    # Just one request - should trigger instant block
    log_line = f'{new_russian_ip} - - [{timestamp}] "GET /test.php HTTP/1.1" 404 0 "-" "Mozilla/5.0"\n'
    f.write(log_line)
    
print(f'Added test log from {new_russian_ip}')
print(f'IDS should instantly block this IP (no threshold wait)')
print()
print(f'Check intrusion_detector.log for:')
print(f'  [ALERT] Russia IP - Geographic Block from {new_russian_ip}')
print(f'  [BLOCKED] IP {new_russian_ip} blocked')
print()
print(f'Check Cloudflare IP Access Rules for new rule with {new_russian_ip}')
