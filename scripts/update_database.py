import asyncio
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.database import engine, Base
from app.models import (
    User,
    UserSession,
    Topic,
    ContentItem,
    UserInteraction,
    UserInterestProfile,
)


async def update_database():
    """Update database schema to match models"""
    print("Updating database schema...")

    try:
        # This will create any missing tables and update schema
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Database schema updated successfully!")

        # Remove deprecated topics and related content
        async with engine.begin() as conn:
            # Delete topics in deprecated categories
            res1 = await conn.execute(text(
                "DELETE FROM topics WHERE category IN ('Reference','Search Query','Trending')"
            ))
            print(f"🗑️ Removed topics in deprecated categories: {getattr(res1, 'rowcount', 'unknown')}" )

            # Delete content items whose topic no longer exists (orphaned)
            res2 = await conn.execute(text(
                "DELETE FROM content_items WHERE topic_id NOT IN (SELECT id FROM topics)"
            ))
            print(f"🗑️ Removed orphaned content items: {getattr(res2, 'rowcount', 'unknown')}" )

    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(update_database())
