#!/usr/bin/env python3
"""Backfill scraped_at timestamp for existing content with content_text"""

import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, ".")

from app.db import AsyncSessionLocal
from app.models import ContentItem


async def backfill_scraped_at():
    """Set scraped_at for all items that have content_text but no scraped_at"""
    async with AsyncSessionLocal() as db:
        # Get all items with content_text but no scraped_at
        result = await db.execute(
            select(ContentItem).where(
                (ContentItem.content_text.isnot(None))
                & (
                    (
                        ContentItem.source_metadata.op("->")("scraped_at").astext.is_(
                            None
                        )
                    )
                    | (ContentItem.source_metadata.is_(None))
                )
            )
        )
        items = result.scalars().all()

        count = 0
        for item in items:
            if not item.source_metadata:
                item.source_metadata = {}

            # Only set if not already set
            if not item.source_metadata.get("scraped_at"):
                item.source_metadata["scraped_at"] = datetime.now(
                    timezone.utc
                ).isoformat()
                count += 1

        if count > 0:
            await db.commit()
            print(f"✅ Backfilled scraped_at for {count} items")
        else:
            print("ℹ️ All items already have scraped_at set")


if __name__ == "__main__":
    asyncio.run(backfill_scraped_at())
