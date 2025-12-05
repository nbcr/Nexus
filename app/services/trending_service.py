import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from sqlalchemy import select  # type: ignore

from app.models import Topic, ContentItem
from app.core.config import settings
from app.services.deduplication import deduplication_service
from app.services.article_scraper import article_scraper
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


class TrendingService:
    def __init__(self):
        self.failure_tracker = FeedFailureTracker(max_failures=5)
        # Multiple RSS feeds for diverse content
        self.rss_feeds = {
            "google_trends": {
                "url": "https://trends.google.com/trending/rss?geo=CA",
                "category_hint": None,  # Auto-categorize
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
        self.reddit_enabled = True
        print(f"✅ Configured {len(self.rss_feeds)} RSS feeds")

    async def fetch_canada_trends(self) -> List[Dict]:
        """Fetch trending topics from multiple RSS feeds and Reddit"""
        trends = []

        # Fetch from all RSS feeds
        rss_trends = await self._fetch_all_rss_feeds()
        trends.extend(rss_trends)

        # Get Reddit trending posts (many more items)
        if self.reddit_enabled:
            reddit_trends = await self._fetch_reddit_trends()
            trends.extend(reddit_trends)

        print(
            f"✅ Total trends fetched: {len(trends)} (RSS: {len(rss_trends)}, Reddit: {len(reddit_trends) if self.reddit_enabled else 0})"
        )
        return trends

    async def _fetch_all_rss_feeds(self) -> List[Dict]:
        """Fetch from all configured RSS feeds in parallel with timeout"""
        self.failure_tracker.reset_if_needed()

        # Create tasks for all enabled feeds
        tasks = []
        feed_names = []

        for feed_name, feed_config in self.rss_feeds.items():
            if self.failure_tracker.is_disabled(feed_name):
                print(f"⏭️ Skipping disabled feed: {feed_name}")
                continue

            print(f"📡 Queuing {feed_name}: {feed_config['url']}")
            task = self._fetch_single_rss_feed_with_timeout(
                feed_name,
                feed_config["url"],
                feed_config.get("category_hint"),
                timeout=8,  # 8 second timeout per feed
            )
            tasks.append(task)
            feed_names.append(feed_name)

        # Fetch all feeds in parallel
        print(f"🚀 Fetching {len(tasks)} feeds in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
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

    async def _fetch_single_rss_feed_with_timeout(
        self,
        feed_name: str,
        feed_url: str,
        category_hint: Optional[str] = None,
        timeout: int = 8,
    ) -> List[Dict]:
        """Fetch a single RSS feed with timeout using async parser"""
        try:
            # Use async RSS parser (no blocking operations)
            feed = await asyncio.wait_for(
                async_rss_parser.parse_feed(feed_url), timeout=timeout
            )

            # Process feed entries
            return await self._process_feed_entries(
                feed, feed_url, category_hint, feed_name
            )
        except asyncio.TimeoutError:
            print(f"⏱️ Timeout fetching {feed_name} after {timeout}s")
            raise TimeoutError(f"Feed {feed_name} timed out")
        except Exception as e:
            print(f"❌ Error in {feed_name}: {e}")
            raise

    async def _process_feed_entries(
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

            for entry in feed.entries[:20]:  # Limit to 20 items per feed
                # Extract basic data (works for all RSS feeds)
                title = getattr(entry, "title", "").strip()
                description = getattr(entry, "summary", "") or getattr(
                    entry, "description", ""
                )
                url = getattr(entry, "link", "")

                # Skip if no title or URL
                if not title or not url:
                    continue

                # For Google Trends, extract special fields
                news_items = []
                image_url = None
                source = source_name

                if is_google_trends:
                    # Google Trends specific extraction
                    news_items = self._extract_google_trends_items(entry)
                    if news_items:
                        first_news = news_items[0]
                        image_url = first_news.get("picture")
                        source = first_news.get("source", source_name)
                    else:
                        image_url = getattr(entry, "ht_picture", None)
                        source = getattr(entry, "ht_picture_source", source_name)

                    title = self._generate_summary_title(title, news_items)
                else:
                    # Standard RSS feed - try to get image from media:content or enclosure
                    if hasattr(entry, "media_content") and entry.media_content:
                        image_url = entry.media_content[0].get("url")
                    elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get("url")
                    elif hasattr(entry, "enclosures") and entry.enclosures:
                        for enc in entry.enclosures:
                            if "image" in enc.get("type", ""):
                                image_url = enc.get("href")
                                break

                    # Create a single news item for standard feeds
                    news_items = [
                        {
                            "title": title,
                            "snippet": description[:200] if description else "",
                            "url": url,
                            "picture": image_url,
                            "source": source_name,
                        }
                    ]

                # Determine category - use hint if provided, otherwise auto-categorize
                if category_hint:
                    category = category_hint
                else:
                    category = self._extract_category(entry)

                trend_data = {
                    "title": title,
                    "original_query": title,
                    "description": description[:500] if description else "",
                    "url": url,
                    "source": source,
                    "image_url": image_url,
                    "published": entry.get("published", ""),
                    "trend_score": 0.6,  # Standard score for RSS items
                    "category": category,
                    "tags": self._extract_tags(entry) + [source_name.lower()],
                    "news_items": news_items,
                }
                trends.append(trend_data)

            return trends

        except Exception as e:
            print(f"❌ Error fetching RSS from {feed_url}: {e}")
            return []

    def _extract_google_trends_items(self, entry) -> List[Dict]:
        """Extract news items specifically from Google Trends RSS entries"""
        news_items = []
        try:
            # Look for individual news item fields
            news_item = {
                "title": getattr(entry, "ht_news_item_title", "").strip(),
                "snippet": getattr(entry, "ht_news_item_snippet", "").strip(),
                "url": getattr(entry, "ht_news_item_url", ""),
                "picture": getattr(entry, "ht_news_item_picture", ""),
                "source": getattr(entry, "ht_news_item_source", "News").strip(),
            }

            # If we have a direct news item with title and URL, add it
            if news_item["title"] and news_item["url"]:
                news_items.append(news_item)

            # Check for nested news items structure
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

    async def _fetch_reddit_trends(self) -> List[Dict]:
        """Fetch trending posts from popular subreddits using Reddit JSON API"""
        trends = []

        try:
            # Popular subreddits with broad appeal
            subreddits = [
                ("all", "Popular"),
                ("worldnews", "World News"),
                ("news", "News"),
                ("technology", "Technology"),
                ("science", "Science"),
                ("sports", "Sports"),
                ("entertainment", "Entertainment"),
                ("todayilearned", "TIL"),
                ("explainlikeimfive", "ELI5"),
                ("askreddit", "AskReddit"),
            ]

            for subreddit_name, category in subreddits:
                try:
                    print(f"Fetching hot posts from r/{subreddit_name}")

                    # Use Reddit's public JSON API (no auth required)
                    url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit=10"
                    headers = {"User-Agent": "Nexus/1.0"}
                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code != 200:
                        print(
                            f"⚠️ Got status {response.status_code} for r/{subreddit_name}"
                        )
                        continue

                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    post_count = 0
                    for post_data in posts:
                        post = post_data.get("data", {})

                        # Skip stickied posts
                        if post.get("stickied", False):
                            continue

                        # Calculate trend score based on upvotes and comments
                        score = post.get("score", 0)
                        num_comments = post.get("num_comments", 0)
                        trend_score = min(
                            0.95, 0.5 + (score / 10000) + (num_comments / 1000)
                        )

                        # Get post thumbnail or preview image
                        image_url = None
                        thumbnail = post.get("thumbnail", "")
                        if thumbnail and thumbnail.startswith("http"):
                            image_url = thumbnail

                        # Try to get better quality image from preview
                        if "preview" in post and "images" in post["preview"]:
                            try:
                                image_url = post["preview"]["images"][0]["source"][
                                    "url"
                                ].replace("&amp;", "&")
                            except:
                                pass

                        # Extract description from selftext or use title
                        description = (
                            post.get("selftext", "")[:500]
                            if post.get("selftext")
                            else f"Posted in r/{subreddit_name}"
                        )

                        trend_data = {
                            "title": post.get("title", "Untitled"),
                            "original_query": post.get("title", "Untitled"),
                            "description": description,
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "source": f"r/{subreddit_name}",
                            "image_url": image_url,
                            "published": datetime.fromtimestamp(
                                post.get("created_utc", 0)
                            ).isoformat(),
                            "trend_score": trend_score,
                            "category": category,
                            "tags": ["reddit", subreddit_name, category.lower()],
                            "news_items": [
                                {
                                    "title": post.get("title", "Untitled"),
                                    "snippet": description,
                                    "url": f"https://reddit.com{post.get('permalink', '')}",
                                    "picture": image_url,
                                    "source": f"r/{subreddit_name}",
                                }
                            ],
                        }
                        trends.append(trend_data)
                        post_count += 1

                    print(f"✅ Added {post_count} posts from r/{subreddit_name}")

                    # Small delay to be respectful to Reddit API
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"⚠️ Error fetching r/{subreddit_name}: {e}")
                    continue

            print(f"✅ Successfully fetched {len(trends)} trends from Reddit")
            return trends

        except Exception as e:
            print(f"❌ Error in _fetch_reddit_trends: {e}")
            return []

    def _extract_news_item(self, entry) -> Dict:
        """Extract news item data from Google Trends entry"""
        news_item = {"source": "News", "picture": None}

        # Look for ht:news_item fields in the entry
        if hasattr(entry, "ht_news_item_source"):
            news_item["source"] = entry.ht_news_item_source
        elif hasattr(entry, "news_item_source"):
            news_item["source"] = entry.news_item_source

        if hasattr(entry, "ht_news_item_picture"):
            news_item["picture"] = entry.ht_news_item_picture
        elif hasattr(entry, "news_item_picture"):
            news_item["picture"] = entry.news_item_picture

        return news_item

    def _calculate_trend_score(self, entry) -> float:
        """Calculate trend score based on position in feed"""
        return 0.7

    # Define comprehensive news categories as class variable
    CATEGORY_KEYWORDS = {
        "Sports": [
            "sport",
            "football",
            "soccer",
            "basketball",
            "hockey",
            "nhl",
            "nfl",
            "nba",
            "mlb",
            "tennis",
            "olympic",
            "athlete",
            "baseball",
            "golf",
            "match",
            "game",
            "player",
            "team",
            "championship",
            "tournament",
            "coach",
            "stadium",
            "league",
            "playoff",
            "score",
            "world cup",
            "super bowl",
            "fifa",
            "ufc",
            "boxing",
            "racing",
            "f1",
            # NHL teams
            "maple leafs",
            "leafs",
            "raptors",
            "oilers",
            "canadiens",
            "habs",
            "canucks",
            "flames",
            "senators",
            "jets",
            "bruins",
            "rangers",
            "penguins",
            "capitals",
            "golden knights",
            "blackhawks",
            "avalanche",
            "panthers",
            "lightning",
            # NBA teams
            "lakers",
            "warriors",
            "celtics",
            "heat",
            "bulls",
            "knicks",
            "nets",
            "clippers",
            "mavericks",
            "spurs",
            # MLB teams
            "blue jays",
            "yankees",
            "red sox",
            "dodgers",
            "giants",
            # Sports trade/roster terms
            "trade rumors",
            "roster",
            "draft",
            "free agent",
            "signing",
            "waiver",
            "lineup",
            "injury report",
            "starting lineup",
        ],
        "Entertainment": [
            "entertainment",
            "movie",
            "film",
            "music",
            "celebrity",
            "tv",
            "show",
            "series",
            "concert",
            "festival",
            "actor",
            "actress",
            "singer",
            "band",
            "album",
            "grammy",
            "oscar",
            "emmy",
            "hollywood",
            "netflix",
            "disney",
            "marvel",
            "streaming",
            "theatre",
            "broadway",
            "comedy",
            "drama",
            "premiere",
            "trailer",
            "box office",
            "artist",
            "musician",
            "song",
            "songwriter",
            "rapper",
            "rock",
            "pop",
            "country",
            "hip hop",
            "jazz",
            "recording",
            "tour",
            "live show",
            "performance",
            "billboard",
            "chart",
            "snl",
            "saturday night live",
            "late night",
            "talk show",
        ],
        "Technology": [
            "tech",
            "ai",
            "artificial intelligence",
            "machine learning",
            "software",
            "hardware",
            "computer",
            "internet",
            "gadget",
            "robot",
            "cyber",
            "smartphone",
            "app",
            "iphone",
            "android",
            "google",
            "apple",
            "microsoft",
            "meta",
            "tesla",
            "bitcoin",
            "crypto",
            "blockchain",
            "data",
            "cloud",
            "security",
            "hack",
            "innovation",
            "digital",
            "online",
            "social media",
            "twitter",
            "facebook",
        ],
        "Business": [
            "business",
            "finance",
            "stock",
            "market",
            "economy",
            "startup",
            "trade",
            "investment",
            "company",
            "entrepreneur",
            "ceo",
            "revenue",
            "profit",
            "loss",
            "merger",
            "acquisition",
            "bankruptcy",
            "earnings",
            "wall street",
            "nasdaq",
            "dow jones",
            "s&p",
            "inflation",
            "recession",
            "gdp",
            "corporate",
            "industry",
        ],
        "Politics": [
            "politics",
            "government",
            "election",
            "policy",
            "law",
            "president",
            "minister",
            "prime minister",
            "congress",
            "senate",
            "parliament",
            "vote",
            "legislation",
            "democrat",
            "republican",
            "liberal",
            "conservative",
            "campaign",
            "candidate",
            "trudeau",
            "biden",
            "trump",
            "political",
            "federal",
            "provincial",
            "municipal",
        ],
        "Health": [
            "health",
            "medicine",
            "medical",
            "doctor",
            "hospital",
            "wellness",
            "fitness",
            "disease",
            "nutrition",
            "vaccine",
            "covid",
            "pandemic",
            "virus",
            "drug",
            "treatment",
            "patient",
            "mental health",
            "therapy",
            "cancer",
            "diabetes",
            "healthcare",
            "pharmacy",
            "clinic",
            "surgery",
            "diagnosis",
            "symptom",
        ],
        "Science": [
            "science",
            "research",
            "study",
            "scientist",
            "discovery",
            "experiment",
            "nasa",
            "space",
            "climate",
            "environment",
            "physics",
            "chemistry",
            "biology",
            "astronomy",
            "planet",
            "mars",
            "rocket",
            "satellite",
            "laboratory",
        ],
        "World News": [
            "international",
            "global",
            "world",
            "foreign",
            "country",
            "nation",
            "war",
            "conflict",
            "peace",
            "treaty",
            "diplomatic",
            "united nations",
            "eu",
            "europe",
            "asia",
            "africa",
            "middle east",
            "crisis",
            "humanitarian",
        ],
        "Crime": [
            "crime",
            "police",
            "arrest",
            "murder",
            "robbery",
            "theft",
            "fraud",
            "investigation",
            "court",
            "trial",
            "verdict",
            "guilty",
            "innocent",
            "sentence",
            "prison",
            "jail",
            "detective",
            "fbi",
            "rcmp",
            "criminal",
            "suspect",
            "shooting",
        ],
        "Weather": [
            "weather",
            "storm",
            "hurricane",
            "tornado",
            "flood",
            "snow",
            "blizzard",
            "temperature",
            "forecast",
            "climate change",
            "wildfire",
            "drought",
            "rain",
            "wind",
            "cold",
            "heat wave",
            "winter",
            "summer",
        ],
        "Education": [
            "education",
            "school",
            "university",
            "college",
            "student",
            "teacher",
            "professor",
            "learning",
            "curriculum",
            "exam",
            "graduation",
            "tuition",
            "campus",
            "academic",
        ],
        "Lifestyle": [
            "lifestyle",
            "fashion",
            "beauty",
            "travel",
            "food",
            "recipe",
            "restaurant",
            "cooking",
            "style",
            "trend",
            "home",
            "decor",
            "design",
            "wedding",
            "relationship",
        ],
    }

    def _categorize_text(self, text: str) -> str:
        """Categorize text based on keywords. Returns best matching category or 'General'.
        Sports and Entertainment keywords get higher priority (1.5x weight) to handle edge cases correctly.
        """
        text_lower = text.lower()
        scores = {cat: 0 for cat in self.CATEGORY_KEYWORDS}

        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            # Sports and Entertainment get priority weighting
            weight = 1.5 if cat in ("Sports", "Entertainment") else 1
            for kw in keywords:
                if kw in text_lower:
                    scores[cat] += weight

        best_category = max(scores, key=scores.get)
        return best_category if scores[best_category] > 0 else "General"

    def _extract_category(self, entry) -> str:
        """Determine category using keywords in title, description, and tags."""
        title = getattr(entry, "title", "")
        description = (
            getattr(entry, "ht_news_item_snippet", "")
            or getattr(entry, "summary", "")
            or getattr(entry, "description", "")
        )
        tags = []
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                if hasattr(tag, "term"):
                    tags.append(tag.term.lower())
        text = f"{title} {description} {' '.join(tags)}"
        return self._categorize_text(text)

    def _extract_tags(self, entry) -> List[str]:
        """Extract tags from entry"""
        tags = ["trending", "canada", "google trends"]
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                if hasattr(tag, "term"):
                    tags.append(tag.term.lower())
        return list(set(tags))

    def _generate_summary_title(
        self, original_title: str, news_items: List[Dict]
    ) -> str:
        """Generate a summary title based on news items and original trend title"""
        try:
            if not news_items:
                return (
                    original_title.title()
                )  # Just capitalize the original title if no news items

            # Get the most recent news item (assuming it's most relevant)
            main_news = news_items[0]

            # Extract key information
            title = main_news.get("title", "").strip()
            snippet = main_news.get("snippet", "").strip()
            source = main_news.get("source", "").strip()

            # If we have a good news title, use it as base
            if title:
                # Clean up the title
                # Remove source names from title if they appear at the start or end
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

                # If the original trend query appears in the title, ensure it's properly highlighted
                if original_title.lower() in title.lower():
                    return title.strip()

                # Otherwise, create a context-aware title
                return f"{original_title.title()}: {title}"

            # Fallback to original title if we couldn't generate a better one
            return original_title.title()

        except Exception as e:
            print(f"Error generating summary title: {e}")
            return original_title.title()

    async def generate_ai_summary(
        self, trend_title: str, trend_description: str = ""
    ) -> str:
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

            # Create new content items for news updates
            # Add microsecond increments to ensure unique timestamps for ordering
            from datetime import datetime, timedelta

            base_time = datetime.utcnow()

            for idx, news_item in enumerate(news_items):
                title = news_item.get("title", "").strip()
                url = news_item.get("url", "")

                # Skip items with no title or URL
                if not title and not url:
                    print(f"  ⊘ Skipping news item with no title or URL")
                    continue

                # Use URL as fallback title if no title provided
                if not title:
                    title = url.split("/")[-1][:100] or "News Update"

                # Check for duplicates
                existing = await deduplication_service.find_duplicate(db, title, url)

                if existing:
                    print(f"  ⚠️ Duplicate found for '{title}' - linking as related")
                    # Link this to the existing content instead of creating new
                    await deduplication_service.link_as_related(
                        db, existing.id, topic_id
                    )
                    continue

                # No duplicate, create new content item
                from app.utils.slug import generate_slug, generate_slug_from_url

                slug = generate_slug(title) if title else generate_slug_from_url(url)
                # Set unique timestamp by adding microseconds - newer items get later timestamps
                created_time = base_time + timedelta(microseconds=idx * 1000)

                # Categorize based on title and snippet
                snippet = news_item.get("snippet", "")
                category_text = f"{title} {snippet}"
                category = self._categorize_text(category_text)

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
                    created_at=created_time,  # Set explicit timestamp
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

    async def save_trends_to_database(self, db: AsyncSession) -> List[Topic]:
        """Fetch trends and save them to database"""
        print("Starting save_trends_to_database...")
        trends = await self.fetch_canada_trends()
        print(f"Fetched {len(trends)} trends from Google Trends")
        saved_topics = []

        if not trends:
            print("Warning: No trends fetched from feed")
            return []

        if not trends:
            print("Warning: No trends fetched from Google Trends")
            return []

        print(f"Processing {len(trends)} trends for database storage")
        for trend_data in trends:
            try:
                normalized_title = trend_data["title"].lower().replace(" ", "_")[:190]
                print(f"Processing trend: {trend_data['title']}")

                # Check if topic already exists
                result = await db.execute(
                    select(Topic).where(Topic.normalized_title == normalized_title)
                )
                existing_topic = result.scalar_one_or_none()

                if existing_topic:
                    print(f"Updating existing topic: {existing_topic.title}")

                    # Use first news item title if available, otherwise keep search term
                    news_items = trend_data.get("news_items", [])
                    if news_items and news_items[0].get("title"):
                        existing_topic.title = news_items[0]["title"]
                    else:
                        existing_topic.title = trend_data["title"]

                    existing_topic.description = trend_data.get("description", "")
                    existing_topic.category = trend_data.get("category", "Trending")
                    existing_topic.trend_score = trend_data.get("trend_score", 0.7)
                    existing_topic.tags = trend_data.get(
                        "tags", ["trending", "canada", "google trends"]
                    )
                    await db.flush()  # Ensure updates are saved

                    # Create new content item for updated news
                    ai_summary = await self.generate_ai_summary(
                        trend_data["title"], trend_data.get("description", "")
                    )

                    from app.utils.slug import generate_slug, generate_slug_from_url

                    title = trend_data.get("title", "").strip()
                    url = trend_data.get("url", "")

                    # Ensure we have a valid title - use topic title or news item title
                    if not title:
                        news_items = trend_data.get("news_items", [])
                        if news_items and news_items[0].get("title"):
                            title = news_items[0]["title"].strip()
                        elif existing_topic.title:
                            title = existing_topic.title
                        else:
                            title = "Trending Update"

                    # Skip creating content if we still don't have a valid title
                    if not title or title == "Trending Update":
                        print(
                            f"  ⚠️ Skipping content item for topic {existing_topic.id} - no valid title"
                        )
                        continue

                    # Try to scrape article and extract facts
                    content_text = ai_summary
                    if url:
                        try:
                            print(f"  📰 Scraping article for facts: {url}")
                            article_data = await article_scraper.fetch_article(url)
                            if article_data and article_data.get("content"):
                                content_text = article_data["content"]
                                print(
                                    f"  ✅ Extracted article content ({len(content_text)} chars)"
                                )
                            else:
                                print(f"  ⚠️ Could not extract content, using summary")
                        except Exception as e:
                            print(f"  ⚠️ Scraping failed: {e}, using summary")

                    slug = (
                        generate_slug(title) if title else generate_slug_from_url(url)
                    )

                    # Prepare source_metadata with image if available
                    source_meta = {
                        "source": trend_data.get("source", "Trends"),
                    }
                    if trend_data.get("image_url"):
                        source_meta["picture_url"] = trend_data["image_url"]

                    # Check for duplicates in OTHER topics (not this one)
                    # Note: We still create the content item to preserve fresh image metadata
                    existing = await deduplication_service.find_duplicate(
                        db, title, url
                    )
                    if existing and existing.topic_id != existing_topic.id:
                        print(
                            f"  ⚠️ Duplicate in different topic found: '{title}' - will link as related"
                        )
                        # Store the related ID in source_metadata instead of skipping
                        source_meta["related_content_ids"] = [existing.id]

                    content_item = ContentItem(
                        topic_id=existing_topic.id,
                        title=title,
                        slug=slug,
                        content_type="trending_analysis",
                        content_text=content_text,
                        ai_model_used="google_trends_analyzer_v1",
                        source_urls=[url],
                        source_metadata=source_meta,
                        is_published=True,
                    )
                    db.add(content_item)

                    # Update news items
                    if trend_data.get("news_items"):
                        await self.update_topic_news_items(
                            db, existing_topic.id, trend_data["news_items"]
                        )

                    saved_topics.append(existing_topic)
                    print(
                        f"🔄 Updated trend: {trend_data['title']} (Source: {trend_data['source']}"
                    )
                else:
                    # Create new topic - use first news item title if available
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
                        tags=trend_data.get(
                            "tags", ["trending", "canada", "google trends"]
                        ),
                    )
                    db.add(topic)
                    await db.flush()

                    ai_summary = await self.generate_ai_summary(
                        trend_data["title"], trend_data.get("description", "")
                    )

                    from app.utils.slug import generate_slug, generate_slug_from_url

                    title = trend_data.get("title", "").strip()
                    url = trend_data.get("url", "")

                    # Ensure we have a valid title - use topic title or news item title
                    if not title:
                        news_items = trend_data.get("news_items", [])
                        if news_items and news_items[0].get("title"):
                            title = news_items[0]["title"].strip()
                        elif topic.title:
                            title = topic.title
                        else:
                            title = "Trending Topic"

                    # Skip creating content if we still don't have a valid title
                    if not title or title == "Trending Topic":
                        print(
                            f"  ⚠️ Skipping content item for topic {topic.id} - no valid title"
                        )
                        continue

                    # Try to scrape article and extract facts
                    content_text = ai_summary
                    if url:
                        try:
                            print(f"  📰 Scraping article for facts: {url}")
                            article_data = await article_scraper.fetch_article(url)
                            if article_data and article_data.get("content"):
                                content_text = article_data["content"]
                                print(
                                    f"  ✅ Extracted article content ({len(content_text)} chars)"
                                )
                            else:
                                print(f"  ⚠️ Could not extract content, using summary")
                        except Exception as e:
                            print(f"  ⚠️ Scraping failed: {e}, using summary")

                    slug = (
                        generate_slug(title) if title else generate_slug_from_url(url)
                    )

                    # Prepare source_metadata with image if available
                    source_meta = {
                        "source": trend_data.get("source", "Trends"),
                    }
                    if trend_data.get("image_url"):
                        source_meta["picture_url"] = trend_data["image_url"]

                    # Check for duplicates in other topics
                    # Note: We still create the content item to preserve fresh image metadata
                    existing = await deduplication_service.find_duplicate(
                        db, title, url
                    )
                    if existing and existing.topic_id != topic.id:
                        print(
                            f"  ⚠️ Duplicate in different topic found: '{title}' - will link as related"
                        )
                        # Store the related ID in source_metadata instead of skipping
                        source_meta["related_content_ids"] = [existing.id]

                    content_item = ContentItem(
                        topic_id=topic.id,
                        title=title,
                        slug=slug,
                        content_type="trending_analysis",
                        content_text=content_text,
                        ai_model_used="google_trends_analyzer_v1",
                        source_urls=[url],
                        source_metadata=source_meta,
                        is_published=True,
                    )
                    db.add(content_item)

                    # Add news items for new topic
                    if trend_data.get("news_items"):
                        await self.update_topic_news_items(
                            db, topic.id, trend_data["news_items"]
                        )

                    saved_topics.append(topic)
                    print(
                        f"✅ Saved new trend: {trend_data['title']} (Source: {trend_data['source']}"
                    )

            except Exception as e:
                print(f"❌ Error saving trend '{trend_data['title']}': {e}")
                continue

        try:
            # Commit all changes
            await db.commit()
            print("✅ Successfully committed all changes to database")

            # Refresh all topics to ensure we have the latest data
            for topic in saved_topics:
                await db.refresh(topic)
                print(f"✅ Refreshed topic: {topic.title}")

            print(f"🎯 Total trends saved/updated in database: {len(saved_topics)}")
            return saved_topics

        except Exception as e:
            print(f"❌ Error finalizing database transaction: {e}")
            await db.rollback()
            raise


# Global instance
trending_service = TrendingService()
