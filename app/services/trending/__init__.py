"""
Trending content service - main facade
Coordinates RSS feeds, Reddit, and database persistence
"""

from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Topic
from .rss_fetcher import RSSFetcher
from .reddit_fetcher import RedditFetcher
from .categorization import ContentCategorizer
from .persistence import TrendingPersistence


class TrendingService:
    """Main service for fetching and managing trending content"""

    GOOGLE_TRENDS_TAG = "google trends"

    def __init__(self):
        self.categorizer = ContentCategorizer()
        self.rss_fetcher = RSSFetcher(self.categorizer)
        self.reddit_fetcher = RedditFetcher()
        self.persistence = TrendingPersistence(self.categorizer)

        print(f"✅ Configured {len(self.rss_fetcher.rss_feeds)} RSS feeds")

    async def fetch_canada_trends(self) -> List[Dict]:
        """Fetch trending topics from multiple RSS feeds and Reddit"""
        trends = []

        rss_trends = await self.rss_fetcher.fetch_all_rss_feeds()
        trends.extend(rss_trends)

        reddit_trends = await self.reddit_fetcher.fetch_reddit_trends()
        trends.extend(reddit_trends)

        print(
            f"✅ Total trends fetched: {len(trends)} (RSS: {len(rss_trends)}, Reddit: {len(reddit_trends)})"
        )
        return trends

    async def save_trends_to_database(self, db: AsyncSession) -> List[Topic]:
        """Fetch trends and save them to database"""
        trends = await self.fetch_canada_trends()
        print(f"Fetched {len(trends)} trends")

        if not trends:
            print("Warning: No trends fetched")
            return []

        return await self.persistence.save_trends_to_database(
            db, trends, self.GOOGLE_TRENDS_TAG
        )

    async def update_topic_news_items(
        self, db: AsyncSession, topic_id: int, news_items: List[Dict]
    ) -> None:
        """Update a topic's news items in the database with deduplication"""
        await self.persistence.update_topic_news_items(db, topic_id, news_items)


# Global instance
trending_service = TrendingService()
