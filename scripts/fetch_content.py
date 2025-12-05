#!/usr/bin/env python3
"""
Content Fetching Script
Fetches trending content from Google Trends and saves to database.
Called by cron job every 15 minutes.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.trending import trending_service
from app.database import AsyncSessionLocal


async def fetch_content():
    """Fetch trending content and save to database"""
    try:
        print(f"📰 Starting content fetch...")
        async with AsyncSessionLocal() as db:
            await trending_service.save_trends_to_database(db)
        print(f"✅ Content fetch completed")
    except Exception as e:
        print(f"❌ Error fetching content: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(fetch_content())
