import asyncio
from app.database import AsyncSessionLocal
from app.models import ContentItem
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        # Find the item by title
        query = select(ContentItem).where(ContentItem.title.ilike('%Meta Quest 3S%'))
        result = await db.execute(query)
        items = result.scalars().all()
        
        for item in items:
            print(f'ID: {item.id}')
            print(f'Title: {item.title}')
            print(f'local_image_path: {item.local_image_path}')
            print(f'source_metadata: {item.source_metadata}')
            print()

asyncio.run(check())
