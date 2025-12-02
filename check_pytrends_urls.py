#!/usr/bin/env python3
"""
Check what URLs PyTrends items have
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ContentItem


async def check_pytrends_urls():
    """Check URLs in PyTrends items"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ContentItem)
            .where(ContentItem.content_type == "trending_analysis")
            .order_by(ContentItem.created_at.desc())
            .limit(10)
        )

        items = result.scalars().all()

        print(f"Found {len(items)} PyTrends items\n")

        for item in items:
            url = item.source_urls[0] if item.source_urls else "None"
            is_search = "duckduckgo.com" in url or "google.com/search" in url
            print(f"ID {item.id}:")
            print(f"  Title: {item.title or 'None'}")
            print(f"  URL: {url}")
            print(f"  Is search URL: {'✓' if is_search else '✗'}")
            print()


if __name__ == "__main__":
    asyncio.run(check_pytrends_urls())
