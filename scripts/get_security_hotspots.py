#!/usr/bin/env python3
"""
Pull security hotspots from SonarQube Cloud using token from .env
"""

import os
import json
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
load_dotenv(env_file)

SONAR_TOKEN = os.getenv("SONAR_TOKEN")
SONAR_URL = "https://sonarcloud.io/api"
PROJECT_KEY = "nbcr_Nexus"

if not SONAR_TOKEN:
    print(f"❌ Error: SONAR_TOKEN not found in .env at {env_file}")
    exit(1)


def get_security_hotspots():
    """Fetch security hotspots from SonarQube Cloud"""
    headers = {
        "Authorization": f"Bearer {SONAR_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Endpoint for security hotspots
    url = f"{SONAR_URL}/hotspots/search"
    
    params = {
        "projectKey": PROJECT_KEY,
        "ps": 500  # Page size (max 500)
    }
    
    try:
        print(f"🔍 Fetching security hotspots from SonarQube Cloud...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        hotspots = data.get("hotspots", [])
        
        print(f"\n✅ Found {len(hotspots)} security hotspots\n")
        
        # Display hotspots
        for i, hotspot in enumerate(hotspots, 1):
            print(f"{i}. {hotspot.get('securityCategory', 'Unknown')}")
            print(f"   File: {hotspot.get('component', 'N/A')}")
            print(f"   Line: {hotspot.get('line', 'N/A')}")
            print(f"   Status: {hotspot.get('status', 'N/A')}")
            print(f"   Risk: {hotspot.get('vulnerabilityProbability', 'N/A')}")
            print(f"   Message: {hotspot.get('message', 'N/A')}")
            print()
        
        # Save to file
        output_file = os.path.join(os.path.dirname(__file__), "..", "security_hotspots.json")
        with open(output_file, "w") as f:
            json.dump(hotspots, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        
        return hotspots
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        return None


def get_hotspot_details(hotspot_key):
    """Get detailed information about a specific hotspot"""
    headers = {
        "Authorization": f"Bearer {SONAR_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"{SONAR_URL}/hotspots/show"
    params = {"hotspot": hotspot_key}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"❌ Error fetching hotspot details: {e}")
    
    return None


if __name__ == "__main__":
    hotspots = get_security_hotspots()
    
    if hotspots and len(hotspots) > 0:
        print("\n" + "="*60)
        print("📋 SECURITY HOTSPOTS SUMMARY")
        print("="*60)
        
        # Group by category
        by_category = {}
        for hotspot in hotspots:
            category = hotspot.get("securityCategory", "Unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(hotspot)
        
        for category, items in sorted(by_category.items()):
            print(f"\n{category}: {len(items)} hotspot(s)")
            for item in items:
                print(f"  - {item.get('component', 'Unknown')}:{item.get('line', '?')}")
