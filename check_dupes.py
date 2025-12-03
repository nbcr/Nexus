"""Check for duplicate content items in the database"""

import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import ContentItem


async def check_duplicates():
    async with AsyncSessionLocal() as db:
        # Find duplicate titles
        result = await db.execute(
            select(ContentItem.title, func.count(ContentItem.id))
            .group_by(ContentItem.title)
            .having(func.count(ContentItem.id) > 1)
            .order_by(func.count(ContentItem.id).desc())
            .limit(20)
        )
        dupes = result.all()

        print("=" * 80)
        print(f"Found {len(dupes)} titles with duplicates:")
        print("=" * 80)
        for title, count in dupes:
            print(f"\n{count}x: {title[:100]}")

            # Get details for this title
            items_result = await db.execute(
                select(ContentItem)
                .where(ContentItem.title == title)
                .order_by(ContentItem.created_at.desc())
            )
            items = items_result.scalars().all()

            for item in items:
                print(
                    f"  - ID: {item.id}, Topic: {item.topic_id}, Created: {item.created_at}"
                )
                if item.source_metadata:
                    pic = item.source_metadata.get("picture_url", "No pic")
                    print(f"    Picture: {pic[:60] if pic != 'No pic' else pic}")


if __name__ == "__main__":
    asyncio.run(check_duplicates())
