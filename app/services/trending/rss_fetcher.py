"""RSS feed fetching and processing for trending content"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import re
from html import unescape

from app.utils.async_rss_parser import get_async_rss_parser


class FeedFailureTracker:
    """Track feed failures and disable feeds that timeout too often"""

    def __init__(self, max_failures: int = 5):
        self.failures = {}  # feed_name -> failure_count
        self.disabled_feeds = set()
        self.max_failures = max_failures
        self.last_reset = datetime.now(timezone.utc)

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
        if datetime.now(timezone.utc) - self.last_reset > timedelta(days=1):
            print("🔄 Resetting feed failure tracking")
            self.failures.clear()
            self.disabled_feeds.clear()
            self.last_reset = datetime.now(timezone.utc)


class RSSFetcher:
    """Fetches and processes RSS feeds for trending content"""

    def __init__(self, categorizer, feeds_file: str = "rss_feeds.txt"):
        self.failure_tracker = FeedFailureTracker(max_failures=5)
        self.categorizer = categorizer
        self.feeds_file = feeds_file
        self.rss_feeds = self._load_feeds_from_file()

    def _clean_html_description(self, description: str) -> str:
        """Remove HTML tags and decode entities from RSS description."""
        if not description:
            return ""
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", "", description)
        # Decode HTML entities
        clean = unescape(clean)
        # Remove extra whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _load_feeds_from_file(self) -> Dict:
        """Load RSS feeds from plaintext file"""
        feeds = {}
        try:
            with open(self.feeds_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse: feed_name|url|category_hint|priority
                    parts = line.split("|")
                    if len(parts) == 4:
                        feed_name, url, category_hint, priority = parts
                        feeds[feed_name] = {
                            "url": url,
                            "category_hint": (
                                None if category_hint == "None" else category_hint
                            ),
                            "priority": priority,
                        }
        except FileNotFoundError:
            print(
                f"⚠️ RSS feeds file not found: {self.feeds_file}, using empty feed list"
            )
        except Exception as e:
            print(f"❌ Error loading RSS feeds from file: {e}")

        return feeds

    def add_feed(
        self,
        feed_name: str,
        url: str,
        category_hint: Optional[str] = None,
        priority: str = "medium",
    ) -> bool:
        """Add a new RSS feed and save to file"""
        # Add to in-memory dict
        self.rss_feeds[feed_name] = {
            "url": url,
            "category_hint": category_hint,
            "priority": priority,
        }

        # Append to file
        try:
            with open(self.feeds_file, "a", encoding="utf-8") as f:
                category_str = category_hint if category_hint else "None"
                f.write(f"\n{feed_name}|{url}|{category_str}|{priority}")
            print(f"✅ Added feed '{feed_name}' to {self.feeds_file}")
            return True
        except Exception as e:
            print(f"❌ Error adding feed to file: {e}")
            return False

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
                get_async_rss_parser().parse_feed(feed_url), timeout=timeout
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

            for entry in feed.get("entries", [])[:50]:
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
        # Handle both dict and object-based entries
        if isinstance(entry, dict):
            title = (
                entry.get("title", "").strip()
                if isinstance(entry.get("title"), str)
                else ""
            )
            description = entry.get("summary", "") or entry.get("description", "") or ""
            url = entry.get("link", "") or ""
        else:
            title = getattr(entry, "title", "").strip()
            description = getattr(entry, "summary", "") or getattr(
                entry, "description", ""
            )
            url = getattr(entry, "link", "")

        if not title or not url:
            return None

        news_items, image_url, source = self._extract_standard_data(
            entry,
            source_name,
            title,
            (
                description
                if isinstance(entry, dict)
                else getattr(entry, "summary", "") or getattr(entry, "description", "")
            ),
            url,
        )

        # Always try to categorize based on content first
        category = self.categorizer.extract_category(entry)
        # Only use category_hint as fallback if categorization returns "General"
        if category == "General" and category_hint:
            category = category_hint

        # Clean HTML from description
        clean_description = self._clean_html_description(description)

        return {
            "title": title,
            "original_query": title,
            "description": clean_description[:500] if clean_description else "",
            "url": url,
            "source": source,
            "image_url": image_url,
            "published": entry.get("published", ""),
            "trend_score": 0.7,
            "category": category,
            "tags": self.categorizer.extract_tags(entry, is_google_trends)
            + [source_name.lower()],
            "news_items": news_items,
        }

    def _extract_standard_data(
        self, entry, source_name: str, title: str, description: str, url: str
    ) -> tuple:
        """Extract data from standard RSS entry"""
        image_url = None

        # Handle both dict and object-based entries
        if isinstance(entry, dict):
            if entry.get("media_content"):
                media = entry.get("media_content")
                if isinstance(media, list) and media:
                    image_url = (
                        media[0].get("url") if isinstance(media[0], dict) else None
                    )
                elif isinstance(media, dict):
                    image_url = media.get("url")
            elif entry.get("media_thumbnail"):
                thumb = entry.get("media_thumbnail")
                if isinstance(thumb, list) and thumb:
                    image_url = (
                        thumb[0].get("url") if isinstance(thumb[0], dict) else None
                    )
                elif isinstance(thumb, dict):
                    image_url = thumb.get("url")
            elif entry.get("enclosures"):
                enclosures = entry.get("enclosures")
                if not isinstance(enclosures, list):
                    enclosures = [enclosures] if enclosures else []
                for enc in enclosures:
                    if isinstance(enc, dict) and "image" in enc.get("type", ""):
                        image_url = enc.get("url")
                        break
        else:
            if hasattr(entry, "media_content") and entry.media_content:
                image_url = entry.media_content[0].get("url")
            elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                for enc in entry.enclosures:
                    if "image" in enc.get("type", ""):
                        image_url = enc.get("href")
                        break

        # Clean HTML from snippet
        clean_snippet = self._clean_html_description(description)

        news_items = [
            {
                "title": title,
                "snippet": clean_snippet[:200] if clean_snippet else "",
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
