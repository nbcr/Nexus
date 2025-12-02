import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def test_database():
    """Test database connection and query sample data"""
    async with AsyncSessionLocal() as session:
        # Query topics
        result = await session.execute(text("SELECT COUNT(*) FROM topics"))
        topic_count = result.scalar()
        print(f"✓ Topics in database: {topic_count}")

        # Query content items
        result = await session.execute(text("SELECT COUNT(*) FROM content_items"))
        content_count = result.scalar()
        print(f"✓ Content items in database: {content_count}")

        # Get the sample topic
        result = await session.execute(text("SELECT title, description FROM topics"))
        topics = result.fetchall()
        for topic in topics:
            print(f"✓ Sample topic: {topic[0]} - {topic[1]}")

        # Get the sample content
        result = await session.execute(
            text(
                """
            SELECT t.title, c.content_type, c.ai_model_used 
            FROM content_items c 
            JOIN topics t ON c.topic_id = t.id
        """
            )
        )
        contents = result.fetchall()
        for content in contents:
            print(f"✓ Sample content: {content[0]} ({content[1]} via {content[2]})")

        # Count all tables
        result = await session.execute(
            text(
                """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
            )
        )
        table_count = result.scalar()
        print(f"✓ Total tables in database: {table_count}")


if __name__ == "__main__":
    asyncio.run(test_database())
