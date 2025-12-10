#!/usr/bin/env python3
"""
GeoIP lookup for detecting Russian and Chinese IPs
"""

import requests
import json
from functools import lru_cache

class GeoIPChecker:
    """Check if an IP belongs to Russia or China"""
    
    def __init__(self):
        self.cache = {}
        # IP ranges for Russia and China (major blocks)
        self.russia_ranges = [
            (5, 5), (31, 31), (37, 37), (46, 46), (77, 77), (79, 79),
            (80, 80), (83, 83), (85, 85), (86, 86), (87, 87), (88, 88),
            (89, 89), (91, 91), (92, 92), (93, 93), (94, 94), (95, 95),
            (109, 109), (149, 149), (185, 185), (188, 188), (195, 195),
            (212, 212), (213, 213), (217, 217)
        ]
        
        self.china_ranges = [
            (1, 1), (27, 27), (36, 37), (42, 42), (58, 59), (60, 60),
            (61, 61), (110, 110), (111, 111), (112, 112), (113, 113),
            (114, 114), (115, 115), (116, 116), (117, 117), (118, 118),
            (119, 119), (120, 120), (121, 121), (122, 122), (123, 123),
            (124, 124), (125, 125), (126, 126), (175, 175), (180, 180),
            (182, 182), (183, 183), (202, 202), (203, 203), (210, 210),
            (211, 211), (218, 218), (219, 219), (220, 220), (221, 221),
            (222, 222), (223, 223)
        ]
    
    def get_first_octet(self, ip):
        """Extract first octet from IP"""
        try:
            return int(ip.split('.')[0])
        except:
            return None
    
    def is_russia(self, ip):
        """Check if IP is from Russia (by first octet range)"""
        octet = self.get_first_octet(ip)
        if octet is None:
            return False
        
        for start, end in self.russia_ranges:
            if start <= octet <= end:
                return True
        return False
    
    def is_china(self, ip):
        """Check if IP is from China (by first octet range)"""
        octet = self.get_first_octet(ip)
        if octet is None:
            return False
        
        for start, end in self.china_ranges:
            if start <= octet <= end:
                return True
        return False
    
    def is_blocked_country(self, ip):
        """Check if IP is from Russia or China"""
        return self.is_russia(ip) or self.is_china(ip)
    
    def get_country(self, ip):
        """Get country code for IP"""
        if self.is_russia(ip):
            return 'Russia'
        elif self.is_china(ip):
            return 'China'
        else:
            return 'Other'

# Global instance
geoip = GeoIPChecker()
