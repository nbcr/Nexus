import feedparser  # type: ignore
import asyncio
import requests
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore
from sqlalchemy import select  # type: ignore

from app.models import Topic, ContentItem
from app.core.config import settings
from app.services.pytrends_service import pytrends_service
from app.services.deduplication import deduplication_service


class TrendingService:
    def __init__(self):
        self.feed_url = "https://trends.google.com/trending/rss?geo=CA"
        self.reddit_enabled = True
        print("✅ Reddit JSON API enabled (no auth required)")

    async def fetch_canada_trends(self) -> List[Dict]:
        """Fetch trending topics from Google Trends Canada RSS feed, Reddit, and PyTrends"""
        trends = []
        pytrends_count = 0

        # First, get PyTrends trending searches (optional - may not work due to Google limits)
        pytrends_data = await self._fetch_pytrends_searches()
        if pytrends_data:
            trends.extend(pytrends_data)
            pytrends_count = len(pytrends_data)
            print(f"✅ PyTrends direct search contributed {pytrends_count} trends")

        # Second, get RSS feed trends (10-20 items)
        rss_trends = await self._fetch_rss_trends()
        base_trends_count = len(trends)
        trends.extend(rss_trends)

        # Third, get Reddit trending posts (many more items)
        if self.reddit_enabled:
            reddit_trends = await self._fetch_reddit_trends()
            trends.extend(reddit_trends)

        # Finally, enrich top RSS/Reddit trends with PyTrends related topics and queries
        # This is more reliable than trending_searches() and works even when that's blocked
        if len(rss_trends) > 0:
            print(
                f"🎨 Enriching top {min(3, len(rss_trends))} RSS trends with PyTrends related content..."
            )
            try:
                enriched = await pytrends_service.enrich_trends_with_pytrends(
                    rss_trends[:3], max_topics=3
                )
                # Add only the new related items (skip the original trends we already have)
                new_related = enriched[len(rss_trends[:3]) :]
                trends.extend(new_related)
                pytrends_count += len(new_related)
                print(
                    f"✅ PyTrends enrichment added {len(new_related)} related topics/queries"
                )
            except Exception as e:
                print(f"⚠️ Could not enrich trends with PyTrends: {e}")

        print(
            f"✅ Total trends fetched: {len(trends)} (PyTrends: {pytrends_count}, RSS: {len(rss_trends)}, Reddit: {len(trends) - pytrends_count - len(rss_trends)})"
        )
        return trends

    async def _fetch_pytrends_searches(self) -> List[Dict]:
        """Fetch trending searches using PyTrends"""
        try:
            return await pytrends_service.fetch_trending_searches()
        except Exception as e:
            print(f"❌ Error fetching PyTrends searches: {e}")
            return []

    async def _fetch_rss_trends(self) -> List[Dict]:
        """Fetch trends from RSS feed"""
        try:
            print(f"Fetching from Google Trends RSS: {self.feed_url}")
            feed = feedparser.parse(self.feed_url)

            trends = []
            # Process all available entries
            for entry in feed.entries:
                print(f"Processing entry: {entry}")  # Debug log

                # Extract data from the Google Trends specific fields
                title = getattr(entry, "title", "").strip()
                description = (
                    getattr(entry, "ht_news_item_snippet", "")
                    or getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                )
                url = getattr(entry, "ht_news_item_url", "") or getattr(
                    entry, "link", ""
                )

                # Extract news items
                news_items = []
                try:
                    # Debug print the entry structure
                    print(f"Entry has ht_news_item? {hasattr(entry, 'ht_news_item')}")
                    if hasattr(entry, "ht_news_item"):
                        print(f"News item type: {type(entry.ht_news_item)}")
                        print(f"News item content: {entry.ht_news_item}")

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
                            # Single news item object
                            items = [entry.ht_news_item]

                        for item in items:
                            news_item = {
                                "title": getattr(
                                    item, "ht_news_item_title", ""
                                ).strip(),
                                "snippet": getattr(
                                    item, "ht_news_item_snippet", ""
                                ).strip(),
                                "url": getattr(item, "ht_news_item_url", ""),
                                "picture": getattr(item, "ht_news_item_picture", ""),
                                "source": getattr(
                                    item, "ht_news_item_source", "News"
                                ).strip(),
                            }
                            if news_item["title"] and news_item["url"]:
                                news_items.append(news_item)
                except Exception as e:
                    print(
                        f"Error processing news items for entry {entry.get('title', 'Unknown')}: {str(e)}"
                    )

                # Set the main image and source from the first news item if available
                image_url = None
                source = "News"

                if news_items:
                    first_news = news_items[0]
                    image_url = first_news["picture"]
                    source = first_news["source"]
                else:
                    # Fallback to entry-level ht: attributes if no news items
                    image_url = getattr(entry, "ht_picture", None)
                    source = getattr(entry, "ht_picture_source", "News")

                # Generate a summary title based on news items
                summary_title = self._generate_summary_title(title, news_items)

                trend_data = {
                    "title": summary_title,  # Use the generated summary title
                    "original_query": title,  # Keep the original search term
                    "description": description,
                    "url": url,
                    "source": source,
                    "image_url": image_url,
                    "published": entry.get("published", ""),
                    "trend_score": self._calculate_trend_score(entry),
                    "category": self._extract_category(entry),
                    "tags": self._extract_tags(entry),
                    "news_items": news_items,
                }
                trends.append(trend_data)

            print(f"✅ Successfully fetched {len(trends)} trends from RSS feed")
            return trends

        except Exception as e:
            print(f"❌ Error fetching RSS trends: {e}")
            return []

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

    def _extract_category(self, entry) -> str:
        """Determine category using keywords in title, description, and tags."""
        CATEGORY_KEYWORDS = {
            "Technology": [
                "tech",
                "ai",
                "machine learning",
                "software",
                "hardware",
                "computer",
                "internet",
                "gadget",
                "robot",
                "cyber",
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
            ],
            "Entertainment": [
                "entertainment",
                "movie",
                "film",
                "music",
                "celebrity",
                "tv",
                "show",
                "game",
                "concert",
                "festival",
            ],
            "Sports": [
                "sport",
                "football",
                "soccer",
                "basketball",
                "tennis",
                "olympic",
                "athlete",
                "baseball",
                "golf",
                "match",
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
            ],
            "Politics": [
                "politics",
                "government",
                "election",
                "policy",
                "law",
                "president",
                "minister",
                "congress",
                "senate",
                "vote",
            ],
        }
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
        text = f"{title} {description} {' '.join(tags)}".lower()
        scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    scores[cat] += 1
        best_category = max(scores, key=scores.get)
        return best_category if scores[best_category] > 0 else "General"

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
                title = news_item.get("title", "")
                url = news_item.get("url", "")

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
                content_item = ContentItem(
                    topic_id=topic_id,
                    title=title,
                    slug=slug,
                    description=news_item.get(
                        "snippet", ""
                    ),  # Add the snippet as description
                    category="News",  # Set category to News for news articles
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
                    # Update existing topic with new information
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

                    title = trend_data.get("title", "")
                    url = trend_data.get("url", "")
                    slug = (
                        generate_slug(title) if title else generate_slug_from_url(url)
                    )
                    content_item = ContentItem(
                        topic_id=existing_topic.id,
                        title=title,
                        slug=slug,
                        content_type="trending_analysis",
                        content_text=ai_summary,
                        ai_model_used="google_trends_analyzer_v1",
                        source_urls=[url],
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
                    # Create new topic
                    topic = Topic(
                        title=trend_data["title"],
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

                    title = trend_data.get("title", "")
                    url = trend_data.get("url", "")
                    slug = (
                        generate_slug(title) if title else generate_slug_from_url(url)
                    )
                    content_item = ContentItem(
                        topic_id=topic.id,
                        title=title,
                        slug=slug,
                        content_type="trending_analysis",
                        content_text=ai_summary,
                        ai_model_used="google_trends_analyzer_v1",
                        source_urls=[url],
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
