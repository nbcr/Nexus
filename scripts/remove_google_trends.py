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
            # First, get content items that need to be deleted (those without the tag but with topics that have it)
            result = await db.execute(
                text(
                    """
                    SELECT COUNT(*) FROM content_items ci
                    INNER JOIN topics t ON ci.topic_id = t.id
                    WHERE t.tags::jsonb ? 'google trends'
                    AND NOT (ci.tags::jsonb ? 'google trends')
                """
                )
            )
            indirect_count = result.scalar()
            print(
                f"Found {indirect_count} content items linked to google trends topics"
            )

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

            # Delete view history for affected content items first
            if indirect_count > 0 or content_count > 0:
                result = await db.execute(
                    text(
                        """
                        DELETE FROM content_view_history 
                        WHERE content_id IN (
                            SELECT id FROM content_items 
                            WHERE tags::jsonb ? 'google trends'
                            OR topic_id IN (
                                SELECT id FROM topics 
                                WHERE tags::jsonb ? 'google trends'
                            )
                        )
                    """
                    )
                )
                await db.commit()
                print("Deleted view history for google trends content items")

            # Delete content items linked to google trends topics (via topic_id)
            if indirect_count > 0 or content_count > 0:
                result = await db.execute(
                    text(
                        """
                        DELETE FROM content_items 
                        WHERE tags::jsonb ? 'google trends'
                        OR topic_id IN (
                            SELECT id FROM topics 
                            WHERE tags::jsonb ? 'google trends'
                        )
                    """
                    )
                )
                await db.commit()
                print(
                    f"Deleted {indirect_count + content_count} content items (including linked ones)"
                )

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
