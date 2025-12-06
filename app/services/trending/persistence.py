"""Database persistence operations for trending content"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Topic, ContentItem
from app.services.deduplication import deduplication_service
from app.services.article_scraper import article_scraper
from app.utils.slug import generate_slug, generate_slug_from_url


class TrendingPersistence:
    """Handles database operations for trending content"""

    def __init__(self, categorizer):
        self.categorizer = categorizer

    def generate_ai_summary(self, trend_title: str, trend_description: str = "") -> str:
        """Generate AI summary for trending topics"""
        if trend_description:
            return trend_description
        return f"Trending topic in Canada: {trend_title}"

    async def update_topic_news_items(
        self, db: AsyncSession, topic_id: int, news_items: List[Dict]
    ) -> None:
        """Update a topic's news items in the database with deduplication"""
        try:
            print(f"Updating news items for topic {topic_id}")
            print(f"Number of news items to add: {len(news_items)}")

            base_time = datetime.now(timezone.utc)

            for idx, news_item in enumerate(news_items):
                title = news_item.get("title", "").strip()
                url = news_item.get("url", "")

                if not title and not url:
                    print("  ⊘ Skipping news item with no title or URL")
                    continue

                if not title:
                    title = url.split("/")[-1][:100] or "News Update"

                existing = await deduplication_service.find_duplicate(db, title, url)

                if existing:
                    print(f"  ⚠️ Duplicate found for '{title}' - linking as related")
                    await deduplication_service.link_as_related(
                        db, existing.id, topic_id
                    )
                    continue

                slug = generate_slug(title) if title else generate_slug_from_url(url)

                # Check if slug already exists
                result = await db.execute(
                    select(ContentItem).where(ContentItem.slug == slug)
                )
                if result.scalar_one_or_none():
                    print(f"  ⚠️ Slug already exists for '{title}' - skipping")
                    continue

                created_time = base_time + timedelta(microseconds=idx * 1000)

                snippet = news_item.get("snippet", "")
                category_text = f"{title} {snippet}"
                category = self.categorizer.categorize_text(category_text)

                content_item = ContentItem(
                    topic_id=topic_id,
                    title=title,
                    slug=slug,
                    description=snippet,
                    category=category,
                    content_type="news_update",
                    content_text=news_item.get("snippet", ""),
                    ai_model_used="google_trends_news_v1",
                    source_urls=[url],
                    is_published=True,
                    created_at=created_time,
                    source_metadata={
                        "source": news_item.get("source", "News"),
                        "picture_url": news_item.get("picture", None),
                        "title": title,
                    },
                )
                db.add(content_item)
                print(f"  ✓ Created new content for '{title}'")

            await db.flush()
            print(f"✅ Successfully processed news items for topic {topic_id}")
        except Exception as e:
            print(f"❌ Error updating news items for topic {topic_id}: {str(e)}")
            print("Detailed error:", e.__class__.__name__, str(e))
            raise

    async def save_trends_to_database(
        self, db: AsyncSession, trends: List[Dict], google_trends_tag: str
    ) -> tuple:
        """Save or update trends in database. Returns (saved_topics, new_content_count)"""
        print("Starting save_trends_to_database...")
        print(f"Processing {len(trends)} trends for database storage")
        saved_topics = []
        new_content_count = 0

        if not trends:
            print("Warning: No trends to save")
            return [], 0

        for trend_data in trends:
            try:
                normalized_title = trend_data["title"].lower().replace(" ", "_")[:190]
                print(f"Processing trend: {trend_data['title']}")

                result = await db.execute(
                    select(Topic).where(Topic.normalized_title == normalized_title)
                )
                existing_topic = result.scalar_one_or_none()

                if existing_topic:
                    await self._update_existing_topic(
                        db, existing_topic, trend_data, google_trends_tag
                    )
                    saved_topics.append(existing_topic)
                else:
                    new_topic = await self._create_new_topic(
                        db, trend_data, normalized_title, google_trends_tag
                    )
                    saved_topics.append(new_topic)
                    new_content_count += 1

            except Exception as e:
                print(f"❌ Error saving trend '{trend_data['title']}': {e}")
                continue

        try:
            await db.commit()
            print("✅ Successfully committed all changes to database")

            for topic in saved_topics:
                await db.refresh(topic)
                print(f"✅ Refreshed topic: {topic.title}")

            print(
                f"🎯 Total trends saved/updated in database: {len(saved_topics)} (New: {new_content_count})"
            )
            return saved_topics, new_content_count

        except Exception as e:
            print(f"❌ Error finalizing database transaction: {e}")
            await db.rollback()
            raise

    async def _update_existing_topic(
        self, db: AsyncSession, topic: Topic, trend_data: Dict, google_trends_tag: str
    ) -> None:
        """Update an existing topic with new data"""
        print(f"Updating existing topic: {topic.title}")

        news_items = trend_data.get("news_items", [])
        if news_items and news_items[0].get("title"):
            topic.title = news_items[0]["title"]
        else:
            topic.title = trend_data["title"]

        topic.description = trend_data.get("description", "")
        topic.category = trend_data.get("category", "Trending")
        topic.trend_score = trend_data.get("trend_score", 0.7)
        topic.tags = trend_data.get("tags", ["trending", "canada", google_trends_tag])
        await db.flush()

        if trend_data.get("news_items"):
            await self.update_topic_news_items(db, topic.id, trend_data["news_items"])

        print(
            f"🔄 Updated trend: {trend_data['title']} (Source: {trend_data['source']})"
        )

    async def _create_new_topic(
        self,
        db: AsyncSession,
        trend_data: Dict,
        normalized_title: str,
        google_trends_tag: str,
    ) -> Topic:
        """Create a new topic from trend data"""
        news_items = trend_data.get("news_items", [])
        if news_items and news_items[0].get("title"):
            topic_title = news_items[0]["title"]
        else:
            topic_title = trend_data["title"]

        topic = Topic(
            title=topic_title,
            normalized_title=normalized_title,
            description=trend_data.get("description", ""),
            category=trend_data.get("category", "Trending"),
            trend_score=trend_data.get("trend_score", 0.7),
            tags=trend_data.get("tags", ["trending", "canada", google_trends_tag]),
        )
        db.add(topic)
        await db.flush()

        if trend_data.get("news_items"):
            await self.update_topic_news_items(db, topic.id, trend_data["news_items"])

        print(
            f"✅ Saved new trend: {trend_data['title']} (Source: {trend_data['source']})"
        )
        return topic
