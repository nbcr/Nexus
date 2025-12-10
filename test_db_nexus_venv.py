import asyncio
from app.db import AsyncSessionLocal
from sqlalchemy import text

async def test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM content_items"))
        count = result.scalar()
        print(f"✓ Database connection works, found {count} items")

asyncio.run(test())
