import asyncio
from app.db import AsyncSessionLocal
from app.services.content_recommendation import recommendation_service

async def test():
    async with AsyncSessionLocal() as session:
        try:
            result = await recommendation_service.get_all_feed(db=session, page_size=5)
            print(f'Got {len(result["items"])} items')
        except Exception as e:
            print(f'Error: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()

asyncio.run(test())
