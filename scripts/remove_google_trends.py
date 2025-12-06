"""Remove Google Trends content from database"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


async def remove_google_trends_content():
    """Remove all content items and topics with google trends tag"""

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Count content items with google trends tag
            result = await db.execute(
                text(
                    """
                    SELECT COUNT(*) as count
                    FROM content_items 
                    WHERE tags::jsonb ? 'google trends'
                """
                )
            )
            content_count = result.scalar()
            print(f"Found {content_count} content items with 'google trends' tag")

            # Count topics with google trends tag
            result = await db.execute(
                text(
                    """
                    SELECT COUNT(*) as count
                    FROM topics 
                    WHERE tags::jsonb ? 'google trends'
                """
                )
            )
            topic_count = result.scalar()
            print(f"Found {topic_count} topics with 'google trends' tag")

            # Delete content items first (foreign key constraint)
            if content_count > 0:
                result = await db.execute(
                    text(
                        """
                        DELETE FROM content_items 
                        WHERE tags::jsonb ? 'google trends'
                    """
                    )
                )
                await db.commit()
                print(f"Deleted {content_count} content items")

            # Delete topics after content items
            if topic_count > 0:
                result = await db.execute(
                    text(
                        """
                        DELETE FROM topics 
                        WHERE tags::jsonb ? 'google trends'
                    """
                    )
                )
                await db.commit()
                print(f"Deleted {topic_count} topics")

            print("✅ Successfully removed all Google Trends content")

        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(remove_google_trends_content())
