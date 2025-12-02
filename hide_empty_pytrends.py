#!/usr/bin/env python3
"""
Script to hide existing PyTrends items that don't have meaningful content.
Marks trending_analysis items as unpublished if they lack pictures and substantial content.
"""
import asyncio
from sqlalchemy import select, update, and_, or_, func
from app.database import AsyncSessionLocal
from app.models import ContentItem


async def hide_empty_pytrends():
    """Mark empty PyTrends items as unpublished"""
    async with AsyncSessionLocal() as db:
        # Find all PyTrends items and check them individually
        result = await db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.content_type == "trending_analysis",
                    ContentItem.is_published == True,
                )
            )
        )

        items_to_hide = []
        all_items = result.scalars().all()

        for item in all_items:
            # Check if item lacks both picture and meaningful content
            has_picture = (
                item.source_metadata
                and item.source_metadata.get("picture_url")
                and len(str(item.source_metadata.get("picture_url", ""))) > 10
            )

            has_content = (
                item.content_text
                and not item.content_text.startswith("Trending topic")
                and len(item.content_text) > 200
            )

            # Hide if it has neither picture nor content
            if not has_picture and not has_content:
                items_to_hide.append(item)

        if not items_to_hide:
            print("No empty PyTrends items found to hide.")
            return

        print(f"Found {len(items_to_hide)} empty PyTrends items to hide:")
        for item in items_to_hide:
            print(f"  - {item.title} (ID: {item.id})")

        # Update them to unpublished
        for item in items_to_hide:
            item.is_published = False

        await db.commit()
        print(f"Successfully hid {len(items_to_hide)} empty PyTrends items.")


if __name__ == "__main__":
    asyncio.run(hide_empty_pytrends())
