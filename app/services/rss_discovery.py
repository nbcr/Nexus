"""
RSS Feed Discovery Service

Discovers and fetches relevant RSS feeds based on user interests and preferences.
Uses multiple sources to find feeds matching user's reading patterns.
"""

import asyncio
import aiohttp
import feedparser
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from collections import Counter

from app.models import UserInteraction, ContentItem, Topic, UserInterestProfile
from app.core.config import settings


class RSSDiscoveryService:
    """Service for discovering and managing RSS feeds based on user preferences"""

    # Popular RSS feeds by category
    CURATED_FEEDS = {
        "Technology": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://www.wired.com/feed/rss",
            "https://arstechnica.com/feed/",
            "https://www.cnet.com/rss/news/",
        ],
        "Business": [
            "https://feeds.bloomberg.com/markets/news.rss",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.forbes.com/business/feed/",
            "https://www.reuters.com/markets/",
        ],
        "Sports": [
            "https://www.espn.com/espn/rss/news",
            "https://www.sportsnet.ca/feed/",
            "https://www.thescore.com/rss/news",
            "https://www.cbc.ca/cmlink/rss-sports",
        ],
        "Entertainment": [
            "https://variety.com/feed/",
            "https://www.hollywoodreporter.com/feed/",
            "https://ew.com/feed/",
            "https://www.rollingstone.com/feed/",
        ],
        "Politics": [
            "https://www.politico.com/rss/politics08.xml",
            "https://www.cbc.ca/cmlink/rss-politics",
            "https://www.theglobeandmail.com/politics/rss/",
        ],
        "Health": [
            "https://www.health.com/feed/",
            "https://www.cbc.ca/cmlink/rss-health",
            "https://www.npr.org/rss/rss.php?id=1128",
        ],
        "Science": [
            "https://www.sciencedaily.com/rss/all.xml",
            "https://www.scientificamerican.com/feed/",
            "https://www.space.com/feeds/all",
            "https://phys.org/rss-feed/",
        ],
        "World News": [
            "https://www.bbc.com/news/world/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://www.cbc.ca/cmlink/rss-world",
        ],
    }

    async def analyze_user_preferences(
        self, db: AsyncSession, user_id: Optional[int], session_token: Optional[str]
    ) -> Dict[str, any]:
        """
        Analyze user's reading patterns to determine their preferences.
        
        Returns:
            Dict with:
            - top_categories: List of categories user reads most
            - keywords: Common keywords from content user engages with
            - reading_time_preference: Average time spent reading
            - content_type_preference: Types of content user prefers
        """
        if not user_id and not session_token:
            return self._get_default_preferences()

        # Get user's interaction history
        query = (
            select(UserInteraction, ContentItem, Topic)
            .join(ContentItem, UserInteraction.content_item_id == ContentItem.id)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(
                UserInteraction.created_at
                >= datetime.utcnow() - timedelta(days=30)  # Last 30 days
            )
        )

        if user_id:
            query = query.where(UserInteraction.user_id == user_id)
        elif session_token:
            from app.models import UserSession

            query = query.join(
                UserSession, UserInteraction.session_id == UserSession.id
            ).where(UserSession.session_token == session_token)

        result = await db.execute(query)
        interactions = result.all()

        if not interactions:
            return self._get_default_preferences()

        # Analyze categories
        categories = [topic.category for _, _, topic in interactions if topic.category]
        category_counts = Counter(categories)
        top_categories = [cat for cat, _ in category_counts.most_common(5)]

        # Analyze keywords from titles and tags
        keywords = []
        for _, content, topic in interactions:
            if topic.tags:
                keywords.extend(topic.tags)
            # Extract words from titles
            title_words = (content.title or topic.title or "").lower().split()
            keywords.extend([w for w in title_words if len(w) > 4])

        keyword_counts = Counter(keywords)
        top_keywords = [kw for kw, _ in keyword_counts.most_common(10)]

        # Analyze reading time
        avg_duration = sum(
            interaction.duration_seconds for interaction, _, _ in interactions
        ) / len(interactions)

        # Analyze content types
        content_types = [content.content_type for _, content, _ in interactions]
        content_type_counts = Counter(content_types)

        return {
            "top_categories": top_categories,
            "keywords": top_keywords,
            "avg_reading_duration": avg_duration,
            "content_type_preferences": dict(content_type_counts),
            "total_interactions": len(interactions),
        }

    def _get_default_preferences(self) -> Dict:
        """Return default preferences for new users"""
        return {
            "top_categories": ["Technology", "Business", "Sports"],
            "keywords": [],
            "avg_reading_duration": 60,
            "content_type_preferences": {},
            "total_interactions": 0,
        }

    async def discover_feeds_for_user(
        self, db: AsyncSession, user_id: Optional[int], session_token: Optional[str]
    ) -> List[Dict]:
        """
        Discover RSS feeds tailored to user's preferences.
        
        Returns:
            List of feed dictionaries with:
            - url: Feed URL
            - category: Category it belongs to
            - title: Feed title
            - description: Feed description
            - relevance_score: How relevant to user (0-1)
        """
        # Analyze user preferences
        preferences = await self.analyze_user_preferences(db, user_id, session_token)
        top_categories = preferences["top_categories"]

        discovered_feeds = []

        # Get curated feeds for user's top categories
        for category in top_categories:
            if category in self.CURATED_FEEDS:
                for feed_url in self.CURATED_FEEDS[category]:
                    # Calculate relevance based on category position
                    relevance = 1.0 - (top_categories.index(category) * 0.15)
                    discovered_feeds.append(
                        {
                            "url": feed_url,
                            "category": category,
                            "relevance_score": relevance,
                            "source": "curated",
                        }
                    )

        # If user has explicit interests in profile, add those too
        if user_id:
            profile = await db.get(UserInterestProfile, user_id)
            if profile and profile.interests:
                # Add feeds for explicitly stated interests
                for interest in profile.interests[:5]:  # Top 5 interests
                    interest_lower = interest.lower()
                    # Map interests to categories
                    for category, feeds in self.CURATED_FEEDS.items():
                        if interest_lower in category.lower():
                            for feed_url in feeds:
                                if not any(
                                    f["url"] == feed_url for f in discovered_feeds
                                ):
                                    discovered_feeds.append(
                                        {
                                            "url": feed_url,
                                            "category": category,
                                            "relevance_score": 0.9,
                                            "source": "interest_profile",
                                        }
                                    )

        return discovered_feeds

    async def fetch_feed_content(
        self, feed_url: str, max_items: int = 10
    ) -> List[Dict]:
        """
        Fetch and parse content from an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to return
            
        Returns:
            List of parsed feed items with title, description, url, published date
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=10) as response:
                    if response.status != 200:
                        return []
                    content = await response.text()

            # Parse the RSS feed
            feed = feedparser.parse(content)

            items = []
            for entry in feed.entries[:max_items]:
                items.append(
                    {
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", "")
                        or entry.get("description", ""),
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "author": entry.get("author", ""),
                        "tags": [
                            tag.get("term", "")
                            for tag in entry.get("tags", [])
                            if hasattr(tag, "get")
                        ],
                    }
                )

            return items

        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            return []

    async def get_personalized_rss_content(
        self,
        db: AsyncSession,
        user_id: Optional[int],
        session_token: Optional[str],
        max_items_per_feed: int = 5,
    ) -> List[Dict]:
        """
        Get personalized content from RSS feeds based on user preferences.
        
        Returns:
            List of content items from various RSS feeds, sorted by relevance
        """
        # Discover relevant feeds
        feeds = await self.discover_feeds_for_user(db, user_id, session_token)

        # Fetch content from top feeds
        all_items = []
        tasks = []

        for feed_info in feeds[:10]:  # Top 10 most relevant feeds
            tasks.append(self.fetch_feed_content(feed_info["url"], max_items_per_feed))

        # Fetch all feeds concurrently
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        for feed_info, items in zip(feeds[:10], feed_results):
            if isinstance(items, Exception) or not items:
                continue

            for item in items:
                item["category"] = feed_info["category"]
                item["relevance_score"] = feed_info["relevance_score"]
                all_items.append(item)

        # Sort by relevance score
        all_items.sort(key=lambda x: x["relevance_score"], reverse=True)

        return all_items

    async def suggest_topics_from_preferences(
        self, db: AsyncSession, user_id: Optional[int], session_token: Optional[str]
    ) -> List[str]:
        """
        Suggest topic keywords for RSS feed search based on user preferences.
        
        Returns:
            List of search keywords/topics
        """
        preferences = await self.analyze_user_preferences(db, user_id, session_token)

        suggestions = []

        # Add category-based suggestions
        for category in preferences["top_categories"]:
            suggestions.append(category.lower())

        # Add keyword-based suggestions
        suggestions.extend(preferences["keywords"][:5])

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for item in suggestions:
            if item not in seen:
                seen.add(item)
                unique_suggestions.append(item)

        return unique_suggestions[:10]


# Global instance
rss_discovery_service = RSSDiscoveryService()
