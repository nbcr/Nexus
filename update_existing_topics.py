"""
Script to update topic titles for existing stories in the database.
This will run the topic title logic on stories already in the database.
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Topic, ContentItem
from app.services.trending_service import trending_service


async def update_existing_topics():
    """Update all existing topics with better titles based on their news items"""
    async with AsyncSessionLocal() as db:
        try:
            print("🔄 Fetching all topics from database...")

            # Get all topics
            result = await db.execute(select(Topic))
            topics = result.scalars().all()

            print(f"✅ Found {len(topics)} topics to process")

            updated_count = 0
            for topic in topics:
                try:
                    # Get content items for this topic
                    result = await db.execute(
                        select(ContentItem).where(ContentItem.topic_id == topic.id)
                    )
                    content_items = result.scalars().all()

                    # Find news_update items with better titles
                    news_items = [
                        item
                        for item in content_items
                        if item.content_type == "news_update"
                    ]

                    if news_items and len(news_items) > 0:
                        # Use the first news item's title
                        first_news = news_items[0]
                        if first_news.title and first_news.title != topic.title:
                            # Check if another topic already has this title
                            result = await db.execute(
                                select(Topic).where(Topic.title == first_news.title)
                            )
                            existing = result.scalar_one_or_none()

                            if existing and existing.id != topic.id:
                                print(
                                    f"  ⊘ Skipped: '{topic.title}' (would duplicate '{first_news.title}')"
                                )
                            else:
                                old_title = topic.title
                                topic.title = first_news.title
                                updated_count += 1
                                print(f"  ✓ Updated: '{old_title}' → '{topic.title}'")
                        else:
                            print(f"  ⊘ Skipped: '{topic.title}' (already good)")
                    else:
                        print(
                            f"  ⊘ Skipped: '{topic.title}' (no news items to extract title from)"
                        )

                except Exception as e:
                    print(f"  ❌ Error processing topic {topic.id}: {e}")
                    continue

            # Commit all changes
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
