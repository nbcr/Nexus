import asyncio
import time
from app.db import AsyncSessionLocal
from app.services.content_recommendation import recommendation_service

async def test():
    async with AsyncSessionLocal() as session:
        try:
            start = time.time()
            print('Starting get_all_feed...')
            result = await asyncio.wait_for(
                recommendation_service.get_all_feed(db=session, page_size=20),
                timeout=5.0
            )
            elapsed = time.time() - start
            print(f'Got {len(result["items"])} items in {elapsed:.2f}s')
        except asyncio.TimeoutError:
            print('Query timed out after 5s - database query is hanging')
        except Exception as e:
            print(f'Error: {type(e).__name__}: {e}')

asyncio.run(test())
