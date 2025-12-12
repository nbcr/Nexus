# Security Hotspots Report

Generated: 2025-12-12 08:53:25

**Total Hotspots:** 94

## Summary by Risk Level

- **HIGH:** 2
- **MEDIUM:** 11
- **LOW:** 81

## Hotspots by Category

### auth (2)

#### 1. Review this potentially hard-coded password.

- **File:** `nbcr_Nexus:app/templates/reset-password.html`
- **Line:** 45
- **Risk Level:** HIGH
- **Status:** REVIEWED

#### 2. "password" detected here, review this potentially hard-coded credential.

- **File:** `nbcr_Nexus:scripts/recreate_test_user.py`
- **Line:** 9
- **Risk Level:** HIGH
- **Status:** TO_REVIEW

### dos (5)

#### 1. Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.

- **File:** `nbcr_Nexus:app/services/article_scraper.py`
- **Line:** 271
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 2. Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.

- **File:** `nbcr_Nexus:app/services/content_recommendation.py`
- **Line:** 33
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 3. Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.

- **File:** `nbcr_Nexus:app/services/content_recommendation.py`
- **Line:** 61
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 4. Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.

- **File:** `nbcr_Nexus:intrusion_detector.py`
- **Line:** 102
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 5. Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.

- **File:** `nbcr_Nexus:intrusion_detector.py`
- **Line:** 386
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

### encrypt-data (3)

#### 1. Using ftp protocol is insecure. Use sftp, scp or ftps instead

- **File:** `nbcr_Nexus:app/core/security_config.py`
- **Line:** 59
- **Risk Level:** LOW
- **Status:** REVIEWED

#### 2. Using http protocol is insecure. Use https instead

- **File:** `nbcr_Nexus:app/core/security_config.py`
- **Line:** 140
- **Risk Level:** LOW
- **Status:** REVIEWED

#### 3. Using ftp protocol is insecure. Use sftp, scp or ftps instead

- **File:** `nbcr_Nexus:app/middleware/security_middleware.py`
- **Line:** 107
- **Risk Level:** LOW
- **Status:** REVIEWED

### insecure-conf (1)

#### 1. Make sure creating this cookie without the "secure" flag is safe.

- **File:** `nbcr_Nexus:app/api/v1/deps.py`
- **Line:** 175
- **Risk Level:** LOW
- **Status:** TO_REVIEW

### others (77)

#### 1. Make sure that hashing data is safe here.

- **File:** `nbcr_Nexus:app/utils/slug.py`
- **Line:** 33
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 2. Make sure that hashing data is safe here.

- **File:** `nbcr_Nexus:app/utils/slug.py`
- **Line:** 51
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 3. Make sure that hashing data is safe here.

- **File:** `nbcr_Nexus:scripts/update_cache_bust.py`
- **Line:** 59
- **Risk Level:** LOW
- **Status:** REVIEWED

#### 4. Make sure that sending signals is safe here.

- **File:** `nbcr_Nexus:app/services/reboot_manager.py`
- **Line:** 151
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 5. Make sure publicly writable directories are used safely here.

- **File:** `nbcr_Nexus:app/services/content_refresh.py`
- **Line:** 18
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 6. Make sure publicly writable directories are used safely here.

- **File:** `nbcr_Nexus:app/services/reboot_manager.py`
- **Line:** 27
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 7. Make sure not using resource integrity feature is safe here.

- **File:** `nbcr_Nexus:app/templates/base.html`
- **Line:** 10
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 8. Make sure not using resource integrity feature is safe here.

- **File:** `nbcr_Nexus:app/templates/base.html`
- **Line:** 20
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 9. Make sure not using resource integrity feature is safe here.

- **File:** `nbcr_Nexus:app/templates/index.html`
- **Line:** 9
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 10. Make sure using this hardcoded IP address "1.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 23
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 11. Make sure using this hardcoded IP address "27.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 24
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 12. Make sure using this hardcoded IP address "36.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 25
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 13. Make sure using this hardcoded IP address "42.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 26
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 14. Make sure using this hardcoded IP address "58.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 27
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 15. Make sure using this hardcoded IP address "60.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 28
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 16. Make sure using this hardcoded IP address "61.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 29
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 17. Make sure using this hardcoded IP address "110.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 30
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 18. Make sure using this hardcoded IP address "111.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 31
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 19. Make sure using this hardcoded IP address "112.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 32
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 20. Make sure using this hardcoded IP address "113.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 33
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 21. Make sure using this hardcoded IP address "114.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 34
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 22. Make sure using this hardcoded IP address "115.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 35
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 23. Make sure using this hardcoded IP address "116.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 36
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 24. Make sure using this hardcoded IP address "117.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 37
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 25. Make sure using this hardcoded IP address "118.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 38
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 26. Make sure using this hardcoded IP address "119.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 39
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 27. Make sure using this hardcoded IP address "120.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 40
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 28. Make sure using this hardcoded IP address "121.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 41
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 29. Make sure using this hardcoded IP address "122.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 42
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 30. Make sure using this hardcoded IP address "123.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 43
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 31. Make sure using this hardcoded IP address "124.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 44
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 32. Make sure using this hardcoded IP address "125.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 45
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 33. Make sure using this hardcoded IP address "126.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 46
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 34. Make sure using this hardcoded IP address "175.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 47
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 35. Make sure using this hardcoded IP address "180.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 48
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 36. Make sure using this hardcoded IP address "182.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 49
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 37. Make sure using this hardcoded IP address "183.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 50
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 38. Make sure using this hardcoded IP address "202.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 51
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 39. Make sure using this hardcoded IP address "203.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 52
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 40. Make sure using this hardcoded IP address "210.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 53
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 41. Make sure using this hardcoded IP address "211.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 54
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 42. Make sure using this hardcoded IP address "218.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 55
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 43. Make sure using this hardcoded IP address "219.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 56
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 44. Make sure using this hardcoded IP address "220.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 57
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 45. Make sure using this hardcoded IP address "221.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 58
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 46. Make sure using this hardcoded IP address "222.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 59
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 47. Make sure using this hardcoded IP address "223.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 60
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 48. Make sure using this hardcoded IP address "5.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 67
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 49. Make sure using this hardcoded IP address "31.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 68
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 50. Make sure using this hardcoded IP address "37.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 69
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 51. Make sure using this hardcoded IP address "46.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 70
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 52. Make sure using this hardcoded IP address "77.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 71
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 53. Make sure using this hardcoded IP address "79.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 72
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 54. Make sure using this hardcoded IP address "80.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 73
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 55. Make sure using this hardcoded IP address "83.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 74
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 56. Make sure using this hardcoded IP address "85.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 75
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 57. Make sure using this hardcoded IP address "86.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 76
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 58. Make sure using this hardcoded IP address "87.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 77
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 59. Make sure using this hardcoded IP address "88.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 78
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 60. Make sure using this hardcoded IP address "89.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 79
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 61. Make sure using this hardcoded IP address "91.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 80
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 62. Make sure using this hardcoded IP address "92.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 81
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 63. Make sure using this hardcoded IP address "93.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 82
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 64. Make sure using this hardcoded IP address "94.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 83
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 65. Make sure using this hardcoded IP address "95.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 84
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 66. Make sure using this hardcoded IP address "109.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 85
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 67. Make sure using this hardcoded IP address "149.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 86
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 68. Make sure using this hardcoded IP address "185.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 87
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 69. Make sure using this hardcoded IP address "188.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 88
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 70. Make sure using this hardcoded IP address "195.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 89
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 71. Make sure using this hardcoded IP address "212.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 90
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 72. Make sure using this hardcoded IP address "213.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 91
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 73. Make sure using this hardcoded IP address "217.0.0.0" is safe here.

- **File:** `nbcr_Nexus:block_china_russia.py`
- **Line:** 92
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 74. Make sure using this hardcoded IP address "212.100.200.1" is safe here.

- **File:** `nbcr_Nexus:test_instant_block.py`
- **Line:** 8
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 75. Make sure using this hardcoded IP address "185.220.100.45" is safe here.

- **File:** `nbcr_Nexus:test_russian_attacks.py`
- **Line:** 17
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 76. Make sure using this hardcoded IP address "89.163.128.100" is safe here.

- **File:** `nbcr_Nexus:test_russian_attacks.py`
- **Line:** 18
- **Risk Level:** LOW
- **Status:** TO_REVIEW

#### 77. Make sure using this hardcoded IP address "195.154.200.75" is safe here.

- **File:** `nbcr_Nexus:test_russian_attacks.py`
- **Line:** 19
- **Risk Level:** LOW
- **Status:** TO_REVIEW

### weak-cryptography (6)

#### 1. Make sure that using this pseudorandom number generator is safe here.

- **File:** `nbcr_Nexus:app/static/js/HeaderSession.js`
- **Line:** 17
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 2. Make sure that using this pseudorandom number generator is safe here.

- **File:** `nbcr_Nexus:app/static/js/config.js`
- **Line:** 51
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 3. Make sure that using this pseudorandom number generator is safe here.

- **File:** `nbcr_Nexus:app/static/js/feed-notifier.js`
- **Line:** 39
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 4. Make sure that using this pseudorandom number generator is safe here.

- **File:** `nbcr_Nexus:app/static/js/header.js`
- **Line:** 27
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 5. Make sure that using this pseudorandom number generator is safe here.

- **File:** `nbcr_Nexus:test_russian_attacks.py`
- **Line:** 52
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

#### 6. Make sure that using this pseudorandom number generator is safe here.

- **File:** `nbcr_Nexus:test_russian_attacks.py`
- **Line:** 53
- **Risk Level:** MEDIUM
- **Status:** TO_REVIEW

## Hotspots by Risk Level

### HIGH Risk (2)

1. **auth** - Review this potentially hard-coded password.
   - File: `nbcr_Nexus:app/templates/reset-password.html:45`
   - Status: REVIEWED

2. **auth** - "password" detected here, review this potentially hard-coded credential.
   - File: `nbcr_Nexus:scripts/recreate_test_user.py:9`
   - Status: TO_REVIEW

### MEDIUM Risk (11)

1. **dos** - Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.
   - File: `nbcr_Nexus:app/services/article_scraper.py:271`
   - Status: TO_REVIEW

2. **dos** - Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.
   - File: `nbcr_Nexus:app/services/content_recommendation.py:33`
   - Status: TO_REVIEW

3. **dos** - Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.
   - File: `nbcr_Nexus:app/services/content_recommendation.py:61`
   - Status: TO_REVIEW

4. **dos** - Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.
   - File: `nbcr_Nexus:intrusion_detector.py:102`
   - Status: TO_REVIEW

5. **dos** - Make sure the regex used here, which is vulnerable to polynomial runtime due to backtracking, cannot lead to denial of service.
   - File: `nbcr_Nexus:intrusion_detector.py:386`
   - Status: TO_REVIEW

6. **weak-cryptography** - Make sure that using this pseudorandom number generator is safe here.
   - File: `nbcr_Nexus:app/static/js/HeaderSession.js:17`
   - Status: TO_REVIEW

7. **weak-cryptography** - Make sure that using this pseudorandom number generator is safe here.
   - File: `nbcr_Nexus:app/static/js/config.js:51`
   - Status: TO_REVIEW

8. **weak-cryptography** - Make sure that using this pseudorandom number generator is safe here.
   - File: `nbcr_Nexus:app/static/js/feed-notifier.js:39`
   - Status: TO_REVIEW

9. **weak-cryptography** - Make sure that using this pseudorandom number generator is safe here.
   - File: `nbcr_Nexus:app/static/js/header.js:27`
   - Status: TO_REVIEW

10. **weak-cryptography** - Make sure that using this pseudorandom number generator is safe here.
   - File: `nbcr_Nexus:test_russian_attacks.py:52`
   - Status: TO_REVIEW

11. **weak-cryptography** - Make sure that using this pseudorandom number generator is safe here.
   - File: `nbcr_Nexus:test_russian_attacks.py:53`
   - Status: TO_REVIEW

### LOW Risk (81)

1. **encrypt-data** - Using ftp protocol is insecure. Use sftp, scp or ftps instead
   - File: `nbcr_Nexus:app/core/security_config.py:59`
   - Status: REVIEWED

2. **encrypt-data** - Using http protocol is insecure. Use https instead
   - File: `nbcr_Nexus:app/core/security_config.py:140`
   - Status: REVIEWED

3. **encrypt-data** - Using ftp protocol is insecure. Use sftp, scp or ftps instead
   - File: `nbcr_Nexus:app/middleware/security_middleware.py:107`
   - Status: REVIEWED

4. **insecure-conf** - Make sure creating this cookie without the "secure" flag is safe.
   - File: `nbcr_Nexus:app/api/v1/deps.py:175`
   - Status: TO_REVIEW

5. **others** - Make sure that hashing data is safe here.
   - File: `nbcr_Nexus:app/utils/slug.py:33`
   - Status: TO_REVIEW

6. **others** - Make sure that hashing data is safe here.
   - File: `nbcr_Nexus:app/utils/slug.py:51`
   - Status: TO_REVIEW

7. **others** - Make sure that hashing data is safe here.
   - File: `nbcr_Nexus:scripts/update_cache_bust.py:59`
   - Status: REVIEWED

8. **others** - Make sure that sending signals is safe here.
   - File: `nbcr_Nexus:app/services/reboot_manager.py:151`
   - Status: TO_REVIEW

9. **others** - Make sure publicly writable directories are used safely here.
   - File: `nbcr_Nexus:app/services/content_refresh.py:18`
   - Status: TO_REVIEW

10. **others** - Make sure publicly writable directories are used safely here.
   - File: `nbcr_Nexus:app/services/reboot_manager.py:27`
   - Status: TO_REVIEW

11. **others** - Make sure not using resource integrity feature is safe here.
   - File: `nbcr_Nexus:app/templates/base.html:10`
   - Status: TO_REVIEW

12. **others** - Make sure not using resource integrity feature is safe here.
   - File: `nbcr_Nexus:app/templates/base.html:20`
   - Status: TO_REVIEW

13. **others** - Make sure not using resource integrity feature is safe here.
   - File: `nbcr_Nexus:app/templates/index.html:9`
   - Status: TO_REVIEW

14. **others** - Make sure using this hardcoded IP address "1.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:23`
   - Status: TO_REVIEW

15. **others** - Make sure using this hardcoded IP address "27.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:24`
   - Status: TO_REVIEW

16. **others** - Make sure using this hardcoded IP address "36.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:25`
   - Status: TO_REVIEW

17. **others** - Make sure using this hardcoded IP address "42.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:26`
   - Status: TO_REVIEW

18. **others** - Make sure using this hardcoded IP address "58.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:27`
   - Status: TO_REVIEW

19. **others** - Make sure using this hardcoded IP address "60.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:28`
   - Status: TO_REVIEW

20. **others** - Make sure using this hardcoded IP address "61.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:29`
   - Status: TO_REVIEW

21. **others** - Make sure using this hardcoded IP address "110.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:30`
   - Status: TO_REVIEW

22. **others** - Make sure using this hardcoded IP address "111.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:31`
   - Status: TO_REVIEW

23. **others** - Make sure using this hardcoded IP address "112.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:32`
   - Status: TO_REVIEW

24. **others** - Make sure using this hardcoded IP address "113.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:33`
   - Status: TO_REVIEW

25. **others** - Make sure using this hardcoded IP address "114.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:34`
   - Status: TO_REVIEW

26. **others** - Make sure using this hardcoded IP address "115.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:35`
   - Status: TO_REVIEW

27. **others** - Make sure using this hardcoded IP address "116.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:36`
   - Status: TO_REVIEW

28. **others** - Make sure using this hardcoded IP address "117.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:37`
   - Status: TO_REVIEW

29. **others** - Make sure using this hardcoded IP address "118.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:38`
   - Status: TO_REVIEW

30. **others** - Make sure using this hardcoded IP address "119.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:39`
   - Status: TO_REVIEW

31. **others** - Make sure using this hardcoded IP address "120.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:40`
   - Status: TO_REVIEW

32. **others** - Make sure using this hardcoded IP address "121.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:41`
   - Status: TO_REVIEW

33. **others** - Make sure using this hardcoded IP address "122.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:42`
   - Status: TO_REVIEW

34. **others** - Make sure using this hardcoded IP address "123.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:43`
   - Status: TO_REVIEW

35. **others** - Make sure using this hardcoded IP address "124.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:44`
   - Status: TO_REVIEW

36. **others** - Make sure using this hardcoded IP address "125.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:45`
   - Status: TO_REVIEW

37. **others** - Make sure using this hardcoded IP address "126.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:46`
   - Status: TO_REVIEW

38. **others** - Make sure using this hardcoded IP address "175.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:47`
   - Status: TO_REVIEW

39. **others** - Make sure using this hardcoded IP address "180.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:48`
   - Status: TO_REVIEW

40. **others** - Make sure using this hardcoded IP address "182.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:49`
   - Status: TO_REVIEW

41. **others** - Make sure using this hardcoded IP address "183.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:50`
   - Status: TO_REVIEW

42. **others** - Make sure using this hardcoded IP address "202.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:51`
   - Status: TO_REVIEW

43. **others** - Make sure using this hardcoded IP address "203.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:52`
   - Status: TO_REVIEW

44. **others** - Make sure using this hardcoded IP address "210.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:53`
   - Status: TO_REVIEW

45. **others** - Make sure using this hardcoded IP address "211.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:54`
   - Status: TO_REVIEW

46. **others** - Make sure using this hardcoded IP address "218.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:55`
   - Status: TO_REVIEW

47. **others** - Make sure using this hardcoded IP address "219.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:56`
   - Status: TO_REVIEW

48. **others** - Make sure using this hardcoded IP address "220.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:57`
   - Status: TO_REVIEW

49. **others** - Make sure using this hardcoded IP address "221.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:58`
   - Status: TO_REVIEW

50. **others** - Make sure using this hardcoded IP address "222.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:59`
   - Status: TO_REVIEW

51. **others** - Make sure using this hardcoded IP address "223.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:60`
   - Status: TO_REVIEW

52. **others** - Make sure using this hardcoded IP address "5.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:67`
   - Status: TO_REVIEW

53. **others** - Make sure using this hardcoded IP address "31.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:68`
   - Status: TO_REVIEW

54. **others** - Make sure using this hardcoded IP address "37.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:69`
   - Status: TO_REVIEW

55. **others** - Make sure using this hardcoded IP address "46.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:70`
   - Status: TO_REVIEW

56. **others** - Make sure using this hardcoded IP address "77.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:71`
   - Status: TO_REVIEW

57. **others** - Make sure using this hardcoded IP address "79.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:72`
   - Status: TO_REVIEW

58. **others** - Make sure using this hardcoded IP address "80.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:73`
   - Status: TO_REVIEW

59. **others** - Make sure using this hardcoded IP address "83.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:74`
   - Status: TO_REVIEW

60. **others** - Make sure using this hardcoded IP address "85.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:75`
   - Status: TO_REVIEW

61. **others** - Make sure using this hardcoded IP address "86.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:76`
   - Status: TO_REVIEW

62. **others** - Make sure using this hardcoded IP address "87.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:77`
   - Status: TO_REVIEW

63. **others** - Make sure using this hardcoded IP address "88.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:78`
   - Status: TO_REVIEW

64. **others** - Make sure using this hardcoded IP address "89.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:79`
   - Status: TO_REVIEW

65. **others** - Make sure using this hardcoded IP address "91.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:80`
   - Status: TO_REVIEW

66. **others** - Make sure using this hardcoded IP address "92.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:81`
   - Status: TO_REVIEW

67. **others** - Make sure using this hardcoded IP address "93.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:82`
   - Status: TO_REVIEW

68. **others** - Make sure using this hardcoded IP address "94.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:83`
   - Status: TO_REVIEW

69. **others** - Make sure using this hardcoded IP address "95.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:84`
   - Status: TO_REVIEW

70. **others** - Make sure using this hardcoded IP address "109.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:85`
   - Status: TO_REVIEW

71. **others** - Make sure using this hardcoded IP address "149.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:86`
   - Status: TO_REVIEW

72. **others** - Make sure using this hardcoded IP address "185.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:87`
   - Status: TO_REVIEW

73. **others** - Make sure using this hardcoded IP address "188.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:88`
   - Status: TO_REVIEW

74. **others** - Make sure using this hardcoded IP address "195.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:89`
   - Status: TO_REVIEW

75. **others** - Make sure using this hardcoded IP address "212.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:90`
   - Status: TO_REVIEW

76. **others** - Make sure using this hardcoded IP address "213.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:91`
   - Status: TO_REVIEW

77. **others** - Make sure using this hardcoded IP address "217.0.0.0" is safe here.
   - File: `nbcr_Nexus:block_china_russia.py:92`
   - Status: TO_REVIEW

78. **others** - Make sure using this hardcoded IP address "212.100.200.1" is safe here.
   - File: `nbcr_Nexus:test_instant_block.py:8`
   - Status: TO_REVIEW

79. **others** - Make sure using this hardcoded IP address "185.220.100.45" is safe here.
   - File: `nbcr_Nexus:test_russian_attacks.py:17`
   - Status: TO_REVIEW

80. **others** - Make sure using this hardcoded IP address "89.163.128.100" is safe here.
   - File: `nbcr_Nexus:test_russian_attacks.py:18`
   - Status: TO_REVIEW

81. **others** - Make sure using this hardcoded IP address "195.154.200.75" is safe here.
   - File: `nbcr_Nexus:test_russian_attacks.py:19`
   - Status: TO_REVIEW

