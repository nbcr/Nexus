"""RSS feed fetching and processing for trending content"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.utils.async_rss_parser import async_rss_parser


class FeedFailureTracker:
    """Track feed failures and disable feeds that timeout too often"""

    def __init__(self, max_failures: int = 5):
        self.failures = {}  # feed_name -> failure_count
        self.disabled_feeds = set()
        self.max_failures = max_failures
        self.last_reset = datetime.now()

    def record_failure(self, feed_name: str):
        """Record a failure for a feed"""
        self.failures[feed_name] = self.failures.get(feed_name, 0) + 1
        if self.failures[feed_name] >= self.max_failures:
            self.disabled_feeds.add(feed_name)
            print(f"🚫 Disabled feed '{feed_name}' after {self.max_failures} failures")

    def record_success(self, feed_name: str):
        """Record a success for a feed (reset failure count)"""
        if feed_name in self.failures:
            self.failures[feed_name] = 0

    def is_disabled(self, feed_name: str) -> bool:
        """Check if a feed is disabled"""
        return feed_name in self.disabled_feeds

    def reset_if_needed(self):
        """Reset failure tracking once per day"""
        if datetime.now() - self.last_reset > timedelta(days=1):
            print("🔄 Resetting feed failure tracking")
            self.failures.clear()
            self.disabled_feeds.clear()
            self.last_reset = datetime.now()


class RSSFetcher:
    """Fetches and processes RSS feeds for trending content"""

    def __init__(self, categorizer):
        self.failure_tracker = FeedFailureTracker(max_failures=5)
        self.categorizer = categorizer
        self.rss_feeds = {
            "google_trends": {
                "url": "https://trends.google.com/trending/rss?geo=CA",
                "category_hint": None,
                "priority": "high",
            },
            "cbc_top": {
                "url": "https://www.cbc.ca/cmlink/rss-topstories",
                "category_hint": None,
                "priority": "high",
            },
            "global_news": {
                "url": "https://globalnews.ca/feed/",
                "category_hint": None,
                "priority": "high",
            },
            "tsn": {
                "url": "https://www.tsn.ca/rss",
                "category_hint": "Sports",
                "priority": "medium",
            },
            "betakit": {
                "url": "https://betakit.com/feed/",
                "category_hint": "Technology",
                "priority": "medium",
            },
            "nhl": {
                "url": "https://www.nhl.com/news/rss",
                "category_hint": "Sports",
                "priority": "medium",
            },
        }

    async def fetch_all_rss_feeds(self) -> List[Dict]:
        """Fetch from all configured RSS feeds in parallel with timeout"""
        self.failure_tracker.reset_if_needed()

        tasks = []
        feed_names = []

        for feed_name, feed_config in self.rss_feeds.items():
            if self.failure_tracker.is_disabled(feed_name):
                print(f"⏭️ Skipping disabled feed: {feed_name}")
                continue

            print(f"📡 Queuing {feed_name}: {feed_config['url']}")
            task = self._fetch_single_feed_with_timeout(
                feed_name,
                feed_config["url"],
                feed_config.get("category_hint"),
                timeout=8,
            )
            tasks.append(task)
            feed_names.append(feed_name)

        print(f"🚀 Fetching {len(tasks)} feeds in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_trends = []
        for feed_name, result in zip(feed_names, results):
            if isinstance(result, Exception):
                print(f"⚠️ Error fetching {feed_name}: {result}")
                self.failure_tracker.record_failure(feed_name)
            elif isinstance(result, list):
                all_trends.extend(result)
                print(f"✅ {feed_name}: {len(result)} items")
                self.failure_tracker.record_success(feed_name)
            else:
                print(f"⚠️ Unexpected result from {feed_name}")
                self.failure_tracker.record_failure(feed_name)

        return all_trends

    async def _fetch_single_feed_with_timeout(
        self,
        feed_name: str,
        feed_url: str,
        category_hint: Optional[str] = None,
        timeout: int = 8,
    ) -> List[Dict]:
        """Fetch a single RSS feed with timeout using async parser"""
        try:
            feed = await asyncio.wait_for(
                async_rss_parser.parse_feed(feed_url), timeout=timeout
            )
            return self._process_feed_entries(feed, feed_url, category_hint, feed_name)
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout fetching {feed_name} after {timeout}s")
            raise TimeoutError(f"Feed {feed_name} timed out")
        except Exception as e:
            print(f"❌ Error in {feed_name}: {e}")
            raise

    def _process_feed_entries(
        self,
        feed,
        feed_url: str,
        category_hint: Optional[str] = None,
        source_name: str = "RSS",
    ) -> List[Dict]:
        """Process feed entries and extract trend data"""
        try:
            trends = []
            is_google_trends = "trends.google.com" in feed_url

            for entry in feed.entries[:20]:
                trend_data = self._process_single_entry(
                    entry, is_google_trends, feed_url, category_hint, source_name
                )
                if trend_data:
                    trends.append(trend_data)

            return trends

        except Exception as e:
            print(f"❌ Error fetching RSS from {feed_url}: {e}")
            return []

    def _process_single_entry(
        self,
        entry,
        is_google_trends: bool,
        feed_url: str,
        category_hint: Optional[str],
        source_name: str,
    ) -> Optional[Dict]:
        """Process a single feed entry"""
        title = getattr(entry, "title", "").strip()
        description = getattr(entry, "summary", "") or getattr(entry, "description", "")
        url = getattr(entry, "link", "")

        if not title or not url:
            return None

        news_items, image_url, source = self._extract_entry_data(
            entry, is_google_trends, source_name, title
        )

        category = (
            category_hint if category_hint else self.categorizer.extract_category(entry)
        )

        return {
            "title": title,
            "original_query": title,
            "description": description[:500] if description else "",
            "url": url,
            "source": source,
            "image_url": image_url,
            "published": entry.get("published", ""),
            "trend_score": 0.7,
            "category": category,
            "tags": self.categorizer.extract_tags(entry) + [source_name.lower()],
            "news_items": news_items,
        }

    def _extract_entry_data(
        self, entry, is_google_trends: bool, source_name: str, title: str
    ) -> tuple:
        """Extract news items, image URL, and source from entry"""
        if is_google_trends:
            return self._extract_google_trends_data(entry, source_name, title)
        return self._extract_standard_data(
            entry,
            source_name,
            title,
            getattr(entry, "summary", "") or getattr(entry, "description", ""),
            getattr(entry, "link", ""),
        )

    def _extract_google_trends_data(self, entry, source_name: str, title: str) -> tuple:
        """Extract data from Google Trends entry"""
        news_items = self._extract_google_trends_items(entry)
        if news_items:
            first_news = news_items[0]
            image_url = first_news.get("picture")
            source = first_news.get("source", source_name)
        else:
            image_url = getattr(entry, "ht_picture", None)
            source = getattr(entry, "ht_picture_source", source_name)
        title = self._generate_summary_title(title, news_items)
        return news_items, image_url, source

    def _extract_standard_data(
        self, entry, source_name: str, title: str, description: str, url: str
    ) -> tuple:
        """Extract data from standard RSS entry"""
        image_url = None
        if hasattr(entry, "media_content") and entry.media_content:
            image_url = entry.media_content[0].get("url")
        elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get("url")
        elif hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    image_url = enc.get("href")
                    break

        news_items = [
            {
                "title": title,
                "snippet": description[:200] if description else "",
                "url": url,
                "picture": image_url,
                "source": source_name,
            }
        ]
        return news_items, image_url, source_name

    def _extract_google_trends_items(self, entry) -> List[Dict]:
        """Extract news items specifically from Google Trends RSS entries"""
        news_items = []
        try:
            news_item = {
                "title": getattr(entry, "ht_news_item_title", "").strip(),
                "snippet": getattr(entry, "ht_news_item_snippet", "").strip(),
                "url": getattr(entry, "ht_news_item_url", ""),
                "picture": getattr(entry, "ht_news_item_picture", ""),
                "source": getattr(entry, "ht_news_item_source", "News").strip(),
            }

            if news_item["title"] and news_item["url"]:
                news_items.append(news_item)

            if hasattr(entry, "ht_news_item"):
                items = []
                if isinstance(entry.ht_news_item, list):
                    items = entry.ht_news_item
                elif isinstance(entry.ht_news_item, dict):
                    items = [entry.ht_news_item]
                elif hasattr(entry.ht_news_item, "ht_news_item_title"):
                    items = [entry.ht_news_item]

                for item in items:
                    news_item = {
                        "title": getattr(item, "ht_news_item_title", "").strip(),
                        "snippet": getattr(item, "ht_news_item_snippet", "").strip(),
                        "url": getattr(item, "ht_news_item_url", ""),
                        "picture": getattr(item, "ht_news_item_picture", ""),
                        "source": getattr(item, "ht_news_item_source", "News").strip(),
                    }
                    if news_item["title"] and news_item["url"]:
                        news_items.append(news_item)
        except Exception as e:
            print(f"Error extracting Google Trends items: {e}")

        return news_items

    def _generate_summary_title(
        self, original_title: str, news_items: List[Dict]
    ) -> str:
        """Generate a summary title based on news items and original trend title"""
        try:
            if not news_items:
                return original_title.title()

            main_news = news_items[0]
            title = main_news.get("title", "").strip()
            source = main_news.get("source", "").strip()

            if title:
                for s in [
                    source,
                    "Report:",
                    "BREAKING:",
                    "UPDATE:",
                    "- CNN",
                    "- BBC",
                    "| CBC News",
                ]:
                    title = title.replace(s, "").strip()

                if original_title.lower() in title.lower():
                    return title.strip()

                return f"{original_title.title()}: {title}"

            return original_title.title()

        except Exception as e:
            print(f"Error generating summary title: {e}")
            return original_title.title()
