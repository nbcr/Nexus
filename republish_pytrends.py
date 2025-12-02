#!/usr/bin/env python3
"""
Re-publish hidden PyTrends items so they can be scraped.
"""
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models import ContentItem


async def republish_pytrends():
    """Re-publish all hidden PyTrends items"""
    async with AsyncSessionLocal() as db:
        # Find hidden PyTrends items
        result = await db.execute(
            select(ContentItem).where(
                ContentItem.content_type == "trending_analysis",
                ContentItem.is_published == False,
            )
        )

        items = result.scalars().all()

        if not items:
            print("✅ No hidden PyTrends items found")
            return

        print(f"Found {len(items)} hidden PyTrends items - re-publishing them...")

        for item in items:
            item.is_published = True

        await db.commit()

        print(f"✅ Re-published {len(items)} PyTrends items!")
        print("They will now appear in the feed and can be scraped by users.")


if __name__ == "__main__":
    asyncio.run(republish_pytrends())
