import asyncio
from app.database import AsyncSessionLocal
from app.models import ContentItem

async def check():
    async with AsyncSessionLocal() as db:
        content = await db.get(ContentItem, 458)
        if content:
            print(f"ID: {content.id}")
            print(f"Title: {content.title}")
            print(f"Description length: {len(content.description) if content.description else 0}")
            print(f"Description: {content.description}")

asyncio.run(check())
