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
from app.db import AsyncSessionLocal


class TrendingPersistence:
    """Handles database operations for trending content"""

    def __init__(self, categorizer):
        self.categorizer = categorizer
        self.bad_feeds = {}  # track feeds with bad items: feed_url -> count

    def generate_ai_summary(self, trend_title: str, trend_description: str = "") -> str:
        """Generate AI summary for trending topics"""
        if trend_description:
            return trend_description
        return f"Trending topic in Canada: {trend_title}"

    def _test_scrape_item(self, title: str, url: str, source_url: str) -> bool:
        """Try to scrape an item to see if we can get better content.
        Returns True if scraping got good content, False if feed is bad."""
        if not url:
            return False

        print(f"  Testing scrape for '{title}' from {url}")
        try:
            article_data = article_scraper.fetch_article(url)
            if (
                article_data
                and article_data.get("content")
                and len(article_data.get("content", "")) > 50
            ):
                print(
                    f"  [OK] Scrape successful ({len(article_data['content'])} chars)"
                )
                return True
            else:
                print(f"  [WARN] Scrape got no useful content")
                # Track this bad feed
                self.bad_feeds[source_url] = self.bad_feeds.get(source_url, 0) + 1
                return False
        except Exception as e:
            print(f"  [ERROR] Scrape failed: {e}")
            self.bad_feeds[source_url] = self.bad_feeds.get(source_url, 0) + 1
            return False

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
                    print("  [SKIP] Skipping news item with no title or URL")
                    continue

                if not title:
                    title = url.split("/")[-1][:100] or "News Update"

                # Skip items with empty or trivial descriptions
                snippet = news_item.get("snippet", "").strip()
                if not snippet or snippet.lower() in ("comments", ""):
                    print(
                        f"  [SKIP] Skipping item '{title}' - empty or trivial description"
                    )
                    # Try to scrape to see if we can salvage it
                    source_url = news_item.get("source", "unknown")
                    self._test_scrape_item(title, url, source_url)
                    continue

                existing = await deduplication_service.find_duplicate(db, title, url)

                if existing:
                    print(
                        f"  [LINK] Duplicate found for '{title}' - linking as related"
                    )

                    # If existing item hasn't been scraped yet, scrape it now
                    if url and not (
                        existing.source_metadata
                        and existing.source_metadata.get("scraped_at")
                    ):
                        print(f"  [SCRAPE] Scraping unscraped existing article: {url}")
                        article_data = article_scraper.fetch_article(url)
                        if article_data:
                            existing.content_text = article_data.get("content")
                            if not existing.source_metadata:
                                existing.source_metadata = {}
                            existing.source_metadata["scraped_at"] = datetime.now(
                                timezone.utc
                            ).isoformat()
                            if article_data.get(
                                "image_url"
                            ) and not existing.source_metadata.get("picture_url"):
                                existing.source_metadata["picture_url"] = article_data[
                                    "image_url"
                                ]
                            print(
                                f"  [OK] Scraped and updated existing item with {len(article_data.get('content', ''))} chars"
                            )
                        else:
                            print(f"  [WARN] Scraping failed for existing item")

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
                    print(f"  [SKIP] Slug already exists for '{title}' - skipping")
                    continue

                created_time = base_time + timedelta(microseconds=idx * 1000)

                snippet = news_item.get("snippet", "")
                category_text = f"{title} {snippet}"
                category = self.categorizer.categorize_text(category_text)

                # Don't scrape during initial fetch - use RSS snippet only
                # Scraping will be done on-demand when content is viewed
                image_url = news_item.get("image_url", None) or news_item.get(
                    "picture", None
                )

                content_item = ContentItem(
                    topic_id=topic_id,
                    title=title,
                    slug=slug,
                    description=snippet,
                    category=category,
                    content_type="news_update",
                    content_text=snippet or "",  # Just use snippet for now
                    ai_model_used="google_trends_news_v1",
                    source_urls=[url],
                    is_published=True,
                    created_at=created_time,
                    source_metadata={
                        "source": news_item.get("source", "News"),
                        "picture_url": image_url,
                        "title": title,
                        "scraped_at": None,  # Mark as not scraped yet
                    },
                )
                db.add(content_item)
                print(f"  [OK] Created new content for '{title}'")

            await db.commit()
            print(f"[OK] Successfully processed news items for topic {topic_id}")

            # Fire and forget: scrape articles in background with concurrency limit
            asyncio.create_task(self._scrape_all_new_articles(news_items))
        except Exception as e:
            print(f"[ERROR] Error updating news items for topic {topic_id}: {str(e)}")
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

        # Filter out any trends with google trends tag to prevent them from being created
        filtered_trends = []
        for trend in trends:
            tags = trend.get("tags", [])
            if google_trends_tag not in tags:
                filtered_trends.append(trend)
            else:
                print(
                    f"[SKIP] Skipping trend with google_trends tag: {trend.get('title')}"
                )

        trends = filtered_trends
        if not trends:
            print(
                "Warning: All trends were filtered out (all contained google_trends tag)"
            )
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

            # Report any bad feeds detected
            if self.bad_feeds:
                print(
                    "\n⚠️ Bad feeds detected (consistently providing empty/trivial content):"
                )
                for feed_url, count in sorted(
                    self.bad_feeds.items(), key=lambda x: x[1], reverse=True
                ):
                    print(f"  - {feed_url}: {count} bad items")
                print("Consider removing these feeds from rss_feeds.txt")

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

    async def _scrape_all_new_articles(self, news_items: List[Dict]) -> None:
        """Background task: Scrape articles and download images in parallel"""
        try:
            async with AsyncSessionLocal() as db:
                # Create tasks for all articles with URLs
                tasks = []
                for news_item in news_items:
                    url = news_item.get("url", "")
                    title = news_item.get("title", "").strip()
                    if url and title:
                        tasks.append(self._scrape_and_store_article(title, url, db))

                if not tasks:
                    return

                # Run all scrapes in parallel with semaphore to limit concurrency
                print(f"📰 Starting background scrape of {len(tasks)} articles...")
                semaphore = asyncio.Semaphore(3)  # Max 3 concurrent scrapes

                async def bounded_scrape(task):
                    async with semaphore:
                        return await task

                results = await asyncio.gather(
                    *[bounded_scrape(task) for task in tasks], return_exceptions=True
                )

                # Count successes
                successes = sum(
                    1 for r in results if r and not isinstance(r, Exception)
                )
                print(
                    f"✅ Background scraping complete: {successes}/{len(tasks)} articles scraped"
                )

        except Exception as e:
            print(f"❌ Background scraping failed: {e}")

    async def _scrape_and_store_article(
        self, title: str, url: str, db: AsyncSession
    ) -> bool:
        """Scrape single article and store content + image"""
        try:
            # Fetch article content and image
            article_data = await asyncio.to_thread(article_scraper.fetch_article, url)

            if not article_data or not article_data.get("content"):
                return False

            # Find the content item
            slug = generate_slug(title)
            result = await db.execute(
                select(ContentItem)
                .where(ContentItem.slug == slug)
                .order_by(ContentItem.id.desc())
                .limit(1)
            )
            content = result.scalar_one_or_none()

            if not content:
                return False

            # Store scraped content
            content.content_text = article_data.get("content", "")
            content.facts = article_data.get("content", "")

            # Download and optimize image
            if article_data.get("image_url"):
                try:
                    image_data = await asyncio.to_thread(
                        article_scraper.download_and_optimize_image,
                        article_data["image_url"],
                        content.id,
                    )
                    if image_data:
                        content.image_data = image_data
                        print(f"  ✅ Scraped & stored image for '{title}'")
                except Exception as e:
                    print(f"  ⚠️ Image download failed for '{title}': {e}")

            # Mark as scraped
            if not content.source_metadata:
                content.source_metadata = {}
            content.source_metadata["scraped_at"] = datetime.now(
                timezone.utc
            ).isoformat()

            await db.commit()
            return True

        except Exception as e:
            print(f"  ⚠️ Scrape failed for '{title}': {e}")
            return False
