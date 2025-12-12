#!/usr/bin/env python3
"""
Force content refresh by clearing the last_refresh timestamp
and then triggering the refresh logic
"""
import asyncio
import sys
from datetime import datetime, timezone

# Add the project to path
sys.path.insert(0, "C:\\Nexus")

from app.db import AsyncSessionLocal
from app.services.content_refresh import content_refresh
from app.services.trending import trending_service


async def force_refresh():
    """Force a content refresh"""
    try:
        # Reset the last_refresh so the service thinks content is stale
        content_refresh.last_refresh = None

        print("[*] Forcing content refresh...")
        print(f"[*] Current time: {datetime.now(timezone.utc)}")

        # Call the refresh function
        count = await content_refresh.refresh_content_if_needed()

        if count > 0:
            print(f"[✓] Successfully refreshed! Added {count} new items")
        else:
            print("[!] Refresh completed but no new items added")

        return count

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return 0


if __name__ == "__main__":
    result = asyncio.run(force_refresh())
    sys.exit(0 if result >= 0 else 1)
