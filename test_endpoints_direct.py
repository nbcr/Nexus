import asyncio
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import ContentItem, Topic

async def test_endpoints():
    async with AsyncSessionLocal() as session:
        # Test categories endpoint query
        print("Testing /categories query...")
        try:
            result = await session.execute(
                select(distinct(ContentItem.category)).where(
                    ContentItem.category.isnot(None)
                )
            )
            cats1 = [row[0] for row in result.fetchall() if row[0]]
            print(f"✓ ContentItem categories: {len(cats1)}")
            print(f"  Examples: {cats1[:5]}")
            
            result = await session.execute(
                select(distinct(Topic.category)).where(Topic.category.isnot(None))
            )
            cats2 = [row[0] for row in result.fetchall() if row[0]]
            print(f"✓ Topic categories: {len(cats2)}")
            print(f"  Examples: {cats2[:5]}")
            
            all_cats = sorted(set(cats1 + cats2))
            print(f"✓ Total unique categories: {len(all_cats)}")
            print(f"  All: {all_cats}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

        # Test feed endpoint query
        print("\nTesting /feed query...")
        try:
            from app.services.content_recommendation import recommendation_service
            result = await recommendation_service.get_all_feed(db=session, page_size=5)
            print(f"✓ Feed query successful: {len(result['items'])} items")
            for item in result['items'][:2]:
                print(f"  - {item['title'][:50]}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test_endpoints())
