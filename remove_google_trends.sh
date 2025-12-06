#!/bin/bash
# Remove Google Trends content from database

cd /home/nexus/nexus

sudo -u nexus /home/nexus/nexus/venv/bin/python3 << 'PYTHON_SCRIPT'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

async def remove_google_trends():
    db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://nexus:nexus@localhost:5432/nexus')
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Count content items
        result = await db.execute(text("SELECT COUNT(*) FROM content_items WHERE tags::jsonb ? 'google trends'"))
        content_count = result.scalar()
        print(f'Content items: {content_count}')
        
        # Count topics
        result = await db.execute(text("SELECT COUNT(*) FROM topics WHERE tags::jsonb ? 'google trends'"))
        topic_count = result.scalar()
        print(f'Topics: {topic_count}')
        
        # Delete content items
        if content_count > 0:
            await db.execute(text("DELETE FROM content_items WHERE tags::jsonb ? 'google trends'"))
            print(f'Deleted {content_count} content items')
        
        # Delete topics
        if topic_count > 0:
            await db.execute(text("DELETE FROM topics WHERE tags::jsonb ? 'google trends'"))
            print(f'Deleted {topic_count} topics')
        
        await db.commit()
        print('Done')
    
    await engine.dispose()

asyncio.run(remove_google_trends())
PYTHON_SCRIPT
