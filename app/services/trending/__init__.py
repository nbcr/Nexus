"""
Trending content service - main facade
Coordinates RSS feeds, Reddit, and database persistence
"""

from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Topic
from .rss_fetcher import RSSFetcher
from .categorization import ContentCategorizer
from .persistence import TrendingPersistence


class TrendingService:
    """Main service for fetching and managing trending content"""

    GOOGLE_TRENDS_TAG = "google trends"

    def __init__(self):
        self.categorizer = ContentCategorizer()
        # Fetch 10 items per feed, process all feeds in batches of 20
        # Benchmarked: 490 items total in ~492s with 408s headroom in 15-minute budget
        self.rss_fetcher = RSSFetcher(
            self.categorizer, items_per_feed=10, batch_size=20
        )
        self.persistence = TrendingPersistence(self.categorizer)

        print(f"✅ Configured {len(self.rss_fetcher.rss_feeds)} RSS feeds")

    async def fetch_canada_trends(self) -> List[Dict]:
        """Fetch trending topics from RSS feeds"""
        trends = []

        rss_trends = await self.rss_fetcher.fetch_all_rss_feeds()
        trends.extend(rss_trends)

        print(f"✅ Total trends fetched: {len(trends)} (RSS: {len(rss_trends)})")
        return trends

    async def save_trends_to_database(self, db: AsyncSession) -> tuple:
        """Fetch trends and save them to database. Returns (topics, new_content_count)"""
        trends = await self.fetch_canada_trends()
        print(f"Fetched {len(trends)} trends")

        if not trends:
            print("Warning: No trends fetched")
            return [], 0

        topics, new_content_count = await self.persistence.save_trends_to_database(
            db, trends, self.GOOGLE_TRENDS_TAG
        )

        # Trigger WebSocket notification if new content was created
        if new_content_count > 0:
            try:
                from app.api.v1.routes.websocket import notify_new_content

                await notify_new_content(count=new_content_count)
                print(f"📢 Notified clients of {new_content_count} new items")
            except Exception as e:
                print(f"⚠️ Failed to notify clients: {e}")

        return topics, new_content_count

    async def update_topic_news_items(
        self, db: AsyncSession, topic_id: int, news_items: List[Dict]
    ) -> None:
        """Update a topic's news items in the database with deduplication"""
        await self.persistence.update_topic_news_items(db, topic_id, news_items)


# Global instance
trending_service = TrendingService()
