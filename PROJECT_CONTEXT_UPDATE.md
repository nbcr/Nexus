# 2025-12-11: Reboot Mechanism & Code Cleanup

## Reboot Method
To trigger a server reboot, write `reboot` to the file `temp/nexus_reboot_request`:
```powershell
# From workspace
"reboot" | Set-Content -Path "c:\Nexus\temp\nexus_reboot_request"
# Or via echo (terminal)
echo "reboot" > temp/nexus_reboot_request
```

The reboot manager service monitors this file and removes it once reboot is initiated. Wait ~10 seconds and verify the file is empty to confirm reboot was started.

## Code Quality Fixes
- Fixed `app/services/trending/rss_fetcher.py`: removed timeout parameter, unused feed_url, extracted image extraction logic to reduce cognitive complexity
- Fixed `app/services/article_scraper.py`: extracted fetch retry logic, article processing, and image extraction into separate methods to reduce cognitive complexity from 28→15, 19→15, 25→15
- Replaced set comprehension with `set()` constructor call

## Commits
- ad4fa83: fix: rss_fetcher.py - remove timeout parameter, unused feed_url, reduce complexity
- 447764d: fix: reduce cognitive complexity and extract nested conditionals in article_scraper and rss_fetcher
