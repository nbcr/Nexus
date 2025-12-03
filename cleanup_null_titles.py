"""Clean up content items with NULL titles"""

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ContentItem


async def cleanup_null_titles():
    async with AsyncSessionLocal() as db:
        try:
            print("🔍 Finding content items with NULL titles...")

            # Get all items with NULL titles
            result = await db.execute(
                select(ContentItem).where(ContentItem.title.is_(None))
            )
            items = result.scalars().all()

            print(f"Found {len(items)} items with NULL titles")

            deleted_count = 0
            for item in items:
                # Delete items with no useful data
                print(f"  Deleting content item {item.id} (Topic: {item.topic_id})")
                await db.delete(item)
                deleted_count += 1

            await db.commit()
            print(
                f"\n✅ Successfully deleted {deleted_count} content items with NULL titles"
            )

        except Exception as e:
            print(f"❌ Error cleaning up NULL titles: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(cleanup_null_titles())
