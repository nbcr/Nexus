import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import ContentItem

async def check():
    async with AsyncSessionLocal() as db:
        content = await db.get(ContentItem, 443)
        if content:
            print(f"ID: {content.id}")
            print(f"Title: {content.title}")
            print(f"local_image_path: {content.local_image_path}")
            print(f"thumbnail_url: {content.thumbnail_url}")
            print(f"source_metadata picture_url: {content.source_metadata.get('picture_url') if content.source_metadata else None}")
            print(f"description has img: {'<img' in (content.description or '')}")

asyncio.run(check())
