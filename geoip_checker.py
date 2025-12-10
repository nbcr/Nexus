#!/usr/bin/env python3
"""
GeoIP lookup for detecting Russian and Chinese IPs
"""

import requests
import json
from functools import lru_cache

class GeoIPChecker:
    """Check if an IP belongs to blocked countries"""
    
    def __init__(self):
        self.cache = {}
        
        # BLOCKED COUNTRIES by first octet IP ranges
        self.blocked_countries = {
            'Russia': [
                (5, 5), (31, 31), (37, 37), (46, 46), (77, 77), (79, 79),
                (80, 80), (83, 83), (85, 85), (86, 86), (87, 87), (88, 88),
                (89, 89), (91, 91), (92, 92), (93, 93), (94, 94), (95, 95),
                (109, 109), (149, 149), (185, 185), (188, 188), (195, 195),
                (212, 212), (213, 213), (217, 217)
            ],
            'China': [
                (1, 1), (27, 27), (36, 37), (42, 42), (58, 59), (60, 60),
                (61, 61), (110, 110), (111, 111), (112, 112), (113, 113),
                (114, 114), (115, 115), (116, 116), (117, 117), (118, 118),
                (119, 119), (120, 120), (121, 121), (122, 122), (123, 123),
                (124, 124), (125, 125), (126, 126), (175, 175), (180, 180),
                (182, 182), (183, 183), (202, 202), (203, 203), (210, 210),
                (211, 211), (218, 218), (219, 219), (220, 220), (221, 221),
                (222, 222), (223, 223)
            ],
            'North Korea': [
                (175, 175)
            ],
            'Iran': [
                (15, 15), (16, 16), (17, 17), (25, 25), (39, 39), (45, 45),
                (62, 62), (78, 78), (81, 81), (84, 84), (90, 90), (130, 130),
                (176, 176), (178, 178), (185, 185), (198, 198)
            ],
            'Syria': [
                (5, 5), (46, 46), (109, 109), (188, 188)
            ],
            'Cuba': [
                (192, 192)
            ],
            'Venezuela': [
                (128, 128), (186, 186)
            ],
            'Belarus': [
                (37, 37), (93, 93), (212, 212)
            ],
            'Vietnam': [
                (1, 1), (27, 27), (42, 42), (58, 58), (103, 103), (118, 118),
                (203, 203), (210, 210), (222, 222)
            ],
            'Indonesia': [
                (36, 36), (39, 39), (43, 43), (101, 101), (110, 110), (180, 180),
                (202, 202)
            ],
            'India': [
                (14, 14), (103, 103), (106, 106), (115, 115), (117, 117),
                (119, 119), (202, 202), (203, 203)
            ],
            'Brazil': [
                (177, 177), (187, 187), (191, 191), (200, 200), (201, 201)
            ],
            'Nigeria': [
                (154, 154), (197, 197)
            ],
            'Pakistan': [
                (39, 39), (101, 101), (202, 202)
            ],
            'Thailand': [
                (1, 1), (49, 49), (58, 58), (122, 122), (202, 202)
            ],
            'Philippines': [
                (1, 1), (27, 27), (124, 124), (180, 180), (203, 203)
            ],
            'Malaysia': [
                (27, 27), (175, 175), (202, 202)
            ],
            'Turkmenistan': [
                (5, 5), (212, 212)
            ],
            'North Macedonia': [
                (31, 31), (178, 178), (185, 185)
            ]
        }
    
    def get_first_octet(self, ip):
        """Extract first octet from IP"""
        try:
            return int(ip.split('.')[0])
        except:
            return None
    
    def is_blocked_country(self, ip):
        """Check if IP is from any blocked country"""
        octet = self.get_first_octet(ip)
        if octet is None:
            return False
        
        for country, ranges in self.blocked_countries.items():
            for start, end in ranges:
                if start <= octet <= end:
                    return True
        return False
    
    def get_country(self, ip):
        """Get country name for IP"""
        octet = self.get_first_octet(ip)
        if octet is None:
            return 'Unknown'
        
        for country, ranges in self.blocked_countries.items():
            for start, end in ranges:
                if start <= octet <= end:
                    return country
        return 'Other'

# Global instance
geoip = GeoIPChecker()
