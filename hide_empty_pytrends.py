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
        # Find PyTrends items that should be hidden (no picture AND no substantial content)
        result = await db.execute(
            select(ContentItem).where(
                and_(
                    ContentItem.content_type == 'trending_analysis',
                    ContentItem.is_published == True,
                    # No picture OR picture_url is empty/null
                    or_(
                        ContentItem.source_metadata.is_(None),
                        ContentItem.source_metadata['picture_url'].astext.is_(None),
                        func.length(ContentItem.source_metadata['picture_url'].astext) <= 10
                    ),
                    # AND no meaningful content
                    or_(
                        ContentItem.content_text.is_(None),
                        ContentItem.content_text.startswith('Trending topic'),
                        func.length(ContentItem.content_text) <= 200
                    )
                )
            )
        )
        
        items_to_hide = result.scalars().all()
        
        if not items_to_hide:
            print("✅ No empty PyTrends items found - all clean!")
            return
        
        print(f"Found {len(items_to_hide)} empty PyTrends items to hide:")
        for item in items_to_hide:
            print(f"  - {item.id}: {item.title}")
        
        # Update them to unpublished
        await db.execute(
            update(ContentItem).where(
                and_(
                    ContentItem.content_type == 'trending_analysis',
                    ContentItem.is_published == True,
                    or_(
                        ContentItem.source_metadata.is_(None),
                        ContentItem.source_metadata['picture_url'].astext.is_(None),
                        func.length(ContentItem.source_metadata['picture_url'].astext) <= 10
                    ),
                    or_(
                        ContentItem.content_text.is_(None),
                        ContentItem.content_text.startswith('Trending topic'),
                        func.length(ContentItem.content_text) <= 200
                    )
                )
            ).values(is_published=False)
        )
        
        await db.commit()
        print(f"✅ Successfully hid {len(items_to_hide)} empty PyTrends items!")
        print("These items will become visible again when users click them and they get scraped.")

if __name__ == "__main__":
    asyncio.run(hide_empty_pytrends())
