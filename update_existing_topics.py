"""
Script to update topic titles for existing stories in the database.
This will run the topic title logic on stories already in the database.
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Topic, ContentItem
from app.services.trending import trending_service


async def _get_content_items_for_topic(db: AsyncSession, topic_id: int) -> list:
    """Get content items for a specific topic."""
    result = await db.execute(
        select(ContentItem).where(ContentItem.topic_id == topic_id)
    )
    return result.scalars().all()

async def _check_title_duplicate(db: AsyncSession, title: str, topic_id: int) -> bool:
    """Check if title already exists for another topic."""
    result = await db.execute(
        select(Topic).where(Topic.title == title)
    )
    existing = result.scalar_one_or_none()
    return existing and existing.id != topic_id

def _get_news_items(content_items: list) -> list:
    """Filter content items to get news updates only."""
    return [item for item in content_items if item.content_type == "news_update"]

async def _process_single_topic(db: AsyncSession, topic: Topic) -> bool:
    """Process a single topic for title update."""
    try:
        content_items = await _get_content_items_for_topic(db, topic.id)
        news_items = _get_news_items(content_items)

        if not news_items:
            print(f"  ⊘ Skipped: '{topic.title}' (no news items to extract title from)")
            return False

        first_news = news_items[0]
        if not first_news.title or first_news.title == topic.title:
            print(f"  ⊘ Skipped: '{topic.title}' (already good)")
            return False

        if await _check_title_duplicate(db, first_news.title, topic.id):
            print(f"  ⊘ Skipped: '{topic.title}' (would duplicate '{first_news.title}')")
            return False

        old_title = topic.title
        topic.title = first_news.title
        print(f"  ✓ Updated: '{old_title}' → '{topic.title}'")
        return True

    except Exception as e:
        print(f"  ❌ Error processing topic {topic.id}: {e}")
        return False

async def update_existing_topics():
    """Update all existing topics with better titles based on their news items"""
    async with AsyncSessionLocal() as db:
        try:
            print("🔄 Fetching all topics from database...")

            result = await db.execute(select(Topic))
            topics = result.scalars().all()

            print(f"✅ Found {len(topics)} topics to process")

            updated_count = 0
            for topic in topics:
                if await _process_single_topic(db, topic):
                    updated_count += 1

            await db.commit()
            print(f"\n✅ Successfully updated {updated_count} topics")

        except Exception as e:
            print(f"❌ Error in update_existing_topics: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("Starting topic title update process...")
    asyncio.run(update_existing_topics())
    print("Done!")
