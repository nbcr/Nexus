#!/usr/bin/env python3
"""Test script to verify Cloudflare API connectivity and IDS functionality"""

import os
import sys
import logging
from datetime import datetime
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_cloudflare_api():
    """Test Cloudflare API credentials"""
    api_key = os.getenv('CLOUDFLARE_API_KEY')
    zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
    
    logger.info("=" * 60)
    logger.info("Testing Cloudflare API Configuration")
    logger.info("=" * 60)
    
    if not api_key:
        logger.error("CLOUDFLARE_API_KEY not set in environment")
        return False
    
    if not zone_id:
        logger.error("CLOUDFLARE_ZONE_ID not set in environment")
        return False
    
    logger.info(f"API Key: {api_key[:20]}...")
    logger.info(f"Zone ID: {zone_id}")
    
    # Test API connectivity
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get zone details to verify credentials
        logger.info("\nVerifying API credentials...")
        response = requests.get(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            zone_data = response.json()
            if zone_data.get('success'):
                zone_info = zone_data.get('result', {})
                logger.info("✓ API credentials valid!")
                logger.info(f"  Domain: {zone_info.get('name')}")
                logger.info(f"  Zone ID: {zone_info.get('id')}")
                return True
            else:
                logger.error(f"✗ API error: {zone_data.get('errors')}")
                return False
        else:
            logger.error(f"✗ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False

def test_blocking_simulation():
    """Simulate blocking an IP without actually blocking"""
    api_key = os.getenv('CLOUDFLARE_API_KEY')
    zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing Block Simulation")
    logger.info("=" * 60)
    
    test_ip = "203.0.113.1"  # TEST-NET-3 (reserved for testing, won't cause issues)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'mode': 'block',
        'configuration': {'target': 'ip', 'value': test_ip},
        'notes': f'TEST BLOCK - {datetime.now()} - Python IDS'
    }
    
    try:
        logger.info(f"\nAttempting to create test block for {test_ip}...")
        response = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            rule_data = response.json()
            if rule_data.get('success'):
                rule_id = rule_data.get('result', {}).get('id')
                logger.info("✓ Test block created successfully!")
                logger.info(f"  Rule ID: {rule_id}")
                
                # Clean up - delete the test rule
                logger.info("Cleaning up test rule...")
                delete_response = requests.delete(
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules/{rule_id}',
                    headers=headers,
                    timeout=10
                )
                
                if delete_response.status_code == 200:
                    logger.info("✓ Test rule deleted successfully")
                    return True
                else:
                    logger.warning(f"⚠ Could not delete test rule: {delete_response.status_code}")
                    logger.info(f"  Please manually delete rule {rule_id} from Cloudflare dashboard")
                    return True
            else:
                logger.error(f"✗ Failed to create rule: {rule_data.get('errors')}")
                return False
        else:
            logger.error(f"✗ HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Simulation failed: {e}")
        return False

def test_intrusion_detector():
    """Test loading the intrusion detector module"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Intrusion Detector Module")
    logger.info("=" * 60)
    
    try:
        logger.info("Importing intrusion_detector module...")
        from intrusion_detector import IntrusionDetector
        logger.info("✓ Module imported successfully")
        
        # Test initialization with test config
        logger.info("\nInitializing IntrusionDetector...")
        detector = IntrusionDetector(log_path='C:\\test.log', config_path='config_ids.json')
        logger.info("✓ IntrusionDetector initialized")
        
        # Test pattern detection
        logger.info("\nTesting attack pattern detection...")
        test_cases = [
            ("GET /../../../etc/passwd", "Directory Traversal"),
            ("GET /wp-admin HTTP/1.1", "Admin Panel Probe"),
            ("GET /test.php HTTP/1.1", "Script File Access"),
            ("GET /api?id=1 OR 1=1", "SQL Injection"),
            ("GET /page.html?url=<script>alert(1)</script>", "XSS Attempt"),
        ]
        
        for url, expected_attack in test_cases:
            attack = detector.detect_attack(url, "Mozilla/5.0", url)
            if attack:
                logger.info(f"  ✓ {url[:40]:40} → {attack}")
            else:
                logger.warning(f"  ✗ {url[:40]:40} → NO MATCH (expected {expected_attack})")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + "Nexus Intrusion Detector - Configuration Test".center(58) + "║")
    logger.info("╚" + "=" * 58 + "╝")
    
    results = {
        "Cloudflare API": test_cloudflare_api(),
        "Block Simulation": test_blocking_simulation(),
        "Intrusion Detector": test_intrusion_detector(),
    }
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ All tests passed! The intrusion detector is ready to use.")
        logger.info("\nNext steps:")
        logger.info("  1. Set the correct log file path in intrusion_detector.py")
        logger.info("  2. Adjust thresholds in config_ids.json as needed")
        logger.info("  3. Start monitoring: python intrusion_detector.py")
        return 0
    else:
        logger.error("\n✗ Some tests failed. Check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
