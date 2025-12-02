#!/usr/bin/env python3
"""
Debug script to see actual HTML from DuckDuckGo
"""
import requests

url = "https://duckduckgo.com/?q=khabib+nurmagomedov&ia=web"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

response = requests.get(url, headers=headers, timeout=10)
html = response.text

# Save to file
with open("/tmp/ddg_response.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Saved HTML to /tmp/ddg_response.html")
print(f"Length: {len(html)} chars")
print(f"Status: {response.status_code}")
print("\nFirst 2000 chars:")
print(html[:2000])
