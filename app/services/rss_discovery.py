"""
RSS Feed Discovery Service

Discovers and fetches relevant RSS feeds based on user interests and preferences.
Uses multiple sources to find feeds matching user's reading patterns.
"""

import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from collections import Counter
from urllib.parse import urljoin, urlparse

from app.models import UserInteraction, ContentItem, Topic, UserInterestProfile
from app.core.config import settings
from app.utils.async_rss_parser import get_async_rss_parser


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
                >= datetime.now(timezone.utc) - timedelta(days=30)  # Last 30 days
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
        preferences = await self.analyze_user_preferences(db, user_id, session_token)
        top_categories = preferences["top_categories"]

        discovered_feeds = []

        # Get curated feeds for user's top categories
        discovered_feeds = self._add_category_feeds(top_categories, discovered_feeds)

        # If user has explicit interests in profile, add those too
        if user_id:
            discovered_feeds = await self._add_interest_feeds(
                db, user_id, discovered_feeds
            )

        return discovered_feeds

    def _add_category_feeds(
        self, top_categories: List[str], discovered_feeds: List[Dict]
    ) -> List[Dict]:
        """Add feeds based on user's top categories"""
        for category in top_categories:
            if category in self.CURATED_FEEDS:
                for feed_url in self.CURATED_FEEDS[category]:
                    relevance = 1.0 - (top_categories.index(category) * 0.15)
                    discovered_feeds.append(
                        {
                            "url": feed_url,
                            "category": category,
                            "relevance_score": relevance,
                            "source": "curated",
                        }
                    )
        return discovered_feeds

    async def _add_interest_feeds(
        self, db: AsyncSession, user_id: int, discovered_feeds: List[Dict]
    ) -> List[Dict]:
        """Add feeds based on user's explicit interest profile"""
        profile = await db.get(UserInterestProfile, user_id)
        if not profile or not profile.interests:
            return discovered_feeds

        for interest in profile.interests[:5]:
            discovered_feeds = self._add_feeds_for_interest(interest, discovered_feeds)
        return discovered_feeds

    def _add_feeds_for_interest(
        self, interest: str, discovered_feeds: List[Dict]
    ) -> List[Dict]:
        """Add feeds matching a specific interest"""
        interest_lower = interest.lower()
        for category, feeds in self.CURATED_FEEDS.items():
            if interest_lower in category.lower():
                discovered_feeds = self._append_category_feeds(
                    category, feeds, discovered_feeds
                )
        return discovered_feeds

    def _append_category_feeds(
        self, category: str, feeds: List[str], discovered_feeds: List[Dict]
    ) -> List[Dict]:
        """Append feeds from a category if not already discovered"""
        for feed_url in feeds:
            if not any(f["url"] == feed_url for f in discovered_feeds):
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
        Fetch and parse content from an RSS feed using async parser.

        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to return

        Returns:
            List of parsed feed items with title, description, url, published date
        """
        try:
            # Use async RSS parser with connection pooling
            feed = await get_async_rss_parser().parse_feed(feed_url)

            items = []
            for entry in feed.get("entries", [])[:max_items]:
                items.append(
                    {
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", "")
                        or entry.get("description", ""),
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "author": entry.get("author", ""),
                        "tags": entry.get("tags", []),
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

    async def search_feeds_by_keyword(
        self, keyword: str, max_results: int = 5
    ) -> List[Dict]:
        """
        Search for RSS feeds matching a keyword using multiple strategies.

        Strategies:
        1. Search common RSS patterns on popular sites
        2. Check RSS discovery services
        3. Look for feeds in news aggregator sites

        Args:
            keyword: Topic to search for
            max_results: Maximum number of feeds to return

        Returns:
            List of discovered feeds with metadata
        """
        discovered_feeds = []

        # Strategy 1: Try common RSS feed URL patterns
        keyword_clean = keyword.lower().replace(" ", "-")
        patterns = [
            f"https://feeds.feedburner.com/{keyword_clean}",
            f"https://www.reddit.com/r/{keyword_clean}/.rss",
            f"https://medium.com/feed/tag/{keyword_clean}",
        ]

        for url in patterns:
            feed_info = await self._validate_feed(url)
            if feed_info:
                discovered_feeds.append(feed_info)
                if len(discovered_feeds) >= max_results:
                    return discovered_feeds

        # Strategy 2: Search Google News RSS for the keyword
        google_news_url = f"https://news.google.com/rss/search?q={keyword.replace(' ', '+')}&hl=en-CA&gl=CA&ceid=CA:en"
        feed_info = await self._validate_feed(google_news_url)
        if feed_info:
            discovered_feeds.append(feed_info)

        return discovered_feeds[:max_results]

    async def _validate_feed(self, url: str) -> Optional[Dict]:
        """
        Validate an RSS feed URL and extract metadata.

        Returns:
            Dict with feed info if valid, None otherwise
        """
        try:
            # Use async RSS parser with connection pooling
            feed = await get_async_rss_parser().parse_feed(url)

            # Check if it's a valid feed with entries
            entries = feed.get("entries", [])
            if not entries or len(entries) == 0:
                return None

            # Extract feed metadata
            feed_info = feed.get("feed", {})
            title = feed_info.get("title", "Unknown Feed")
            description = feed_info.get("description", "")

            # Calculate feed quality score
            quality_score = self._calculate_feed_quality(feed)

            return {
                "url": url,
                "title": title,
                "description": description,
                "quality_score": quality_score,
                "total_entries": len(entries),
                "last_updated": feed_info.get("updated", ""),
                "language": feed_info.get("language", "en"),
            }

        except Exception as e:
            print(f"Failed to validate feed {url}: {e}")
            return None

    def _calculate_feed_quality(self, feed) -> float:
        """
        Calculate quality score for an RSS feed (0-1).

        Factors:
        - Update frequency (recent posts)
        - Content length (substantial articles)
        - Number of entries available
        - Feed metadata completeness
        """
        score = 0.5  # Base score

        entries = feed.get("entries", [])
        feed_info = feed.get("feed", {})

        score += self._score_update_recency(entries)
        score += self._score_content_quality(entries)
        score += self._score_entry_count(entries)
        score += self._score_metadata(feed_info)

        return min(score, 1.0)

    def _score_update_recency(self, entries: List) -> float:
        """Score based on how recent the latest entry is"""
        if not entries:
            return 0.0

        try:
            latest_entry = entries[0]
            if not latest_entry.get("published_parsed"):
                return 0.0

            pub_date = datetime(
                *latest_entry["published_parsed"][:6], tzinfo=timezone.utc
            )
            days_old = (datetime.now(timezone.utc) - pub_date).days

            if days_old < 1:
                return 0.2
            if days_old < 7:
                return 0.15
            if days_old < 30:
                return 0.1
            return 0.0
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def _score_content_quality(self, entries: List) -> float:
        """Score based on average content length"""
        if not entries:
            return 0.0

        avg_length = sum(
            len(entry.get("summary", "") or entry.get("description", ""))
            for entry in entries[:5]
        ) / min(5, len(entries))

        if avg_length > 500:
            return 0.15
        if avg_length > 200:
            return 0.1
        return 0.0

    def _score_entry_count(self, entries: List) -> float:
        """Score based on number of available entries"""
        entry_count = len(entries)
        if entry_count > 20:
            return 0.1
        if entry_count > 10:
            return 0.05
        return 0.0

    def _score_metadata(self, feed_info: Dict) -> float:
        """Score based on feed metadata completeness"""
        score = 0.0
        if feed_info.get("title"):
            score += 0.05
        if feed_info.get("description"):
            score += 0.05
        return score

    async def auto_discover_feeds_for_user(
        self,
        db: AsyncSession,
        user_id: Optional[int],
        session_token: Optional[str],
        max_feeds: int = 10,
    ) -> List[Dict]:
        """
        Automatically discover new RSS feeds based on user's preferences.
        Searches for feeds matching user's top keywords and categories.

        Returns:
            List of newly discovered feeds with quality scores
        """
        # Get user preferences
        preferences = await self.analyze_user_preferences(db, user_id, session_token)

        # Get search terms from keywords and categories
        search_terms = []
        search_terms.extend(preferences["keywords"][:5])  # Top 5 keywords
        search_terms.extend(
            [cat.lower() for cat in preferences["top_categories"][:3]]
        )  # Top 3 categories

        # Remove duplicates
        search_terms = list(set(search_terms))

        # Search for feeds
        all_discovered = []
        tasks = []

        for term in search_terms[:5]:  # Search top 5 terms
            tasks.append(self.search_feeds_by_keyword(term, max_results=3))

        # Execute searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        for result in results:
            if isinstance(result, list):
                all_discovered.extend(result)

        # Remove duplicates by URL
        seen_urls = set()
        unique_feeds = []
        for feed in all_discovered:
            if feed["url"] not in seen_urls:
                seen_urls.add(feed["url"])
                unique_feeds.append(feed)

        # Sort by quality score
        unique_feeds.sort(key=lambda x: x["quality_score"], reverse=True)

        # Filter out feeds we already have in curated list and rss_feeds.txt
        existing_urls = set()
        for feeds in self.CURATED_FEEDS.values():
            existing_urls.update(feeds)

        # Also check rss_feeds.txt
        try:
            with open("rss_feeds.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("|")
                    if len(parts) >= 2:
                        existing_urls.add(parts[1])
        except FileNotFoundError:
            pass

        new_feeds = [f for f in unique_feeds if f["url"] not in existing_urls]

        return new_feeds[:max_feeds]


# Global instance
rss_discovery_service = RSSDiscoveryService()
