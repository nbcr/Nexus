#!/usr/bin/env python3
"""
Dynamic RSS Feed Discovery and Management
Automatically finds and adds RSS feeds based on user category preferences.

This script:
1. Analyzes which categories users engage with most
2. Discovers new RSS feeds for those categories
3. Tests feed quality (freshness, content volume, etc.)
4. Adds high-quality feeds to the system
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set
import feedparser
import aiohttp
import aiofiles
from sqlalchemy import text, func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal


# RSS Feed Discovery Sources
FEED_DISCOVERY_APIS = {
    "feedly": "https://feedly.com/v3/search/feeds?query={}",  # Free API
    "feedspot": None,  # Requires scraping
}

# Curated feed database by category
CANDIDATE_FEEDS = {
    "Sports": [
        "https://www.espn.com/espn/rss/news",
        "https://sports.yahoo.com/mlb/rss.xml",
        "https://www.sportsnet.ca/feed/",
        "https://www.si.com/rss/si_topstories.rss",
        "https://www.cbssports.com/rss/headlines",
        "https://www.theringer.com/rss/index.xml",
    ],
    "Technology": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://arstechnica.com/feed/",
        "https://www.wired.com/feed/rss",
        "https://www.engadget.com/rss.xml",
        "https://hacks.mozilla.org/feed/",
        "https://blog.google/rss/",
    ],
    "Entertainment": [
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://ew.com/feed/",
        "https://www.rollingstone.com/feed/",
        "https://pitchfork.com/rss/reviews/albums/",
        "https://www.billboard.com/feed/",
    ],
    "Business": [
        "https://www.bloomberg.com/feed/podcast/bloomberg-businessweek",
        "https://www.wsj.com/xml/rss/3_7014.xml",
        "https://www.businessinsider.com/rss",
        "https://www.forbes.com/real-time/feed2/",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    ],
    "Science": [
        "https://www.nature.com/nature.rss",
        "https://www.sciencedaily.com/rss/all.xml",
        "https://www.newscientist.com/feed/home",
        "https://www.scientificamerican.com/feed/",
        "https://www.space.com/feeds/all",
    ],
    "Health": [
        "https://www.health.com/rss",
        "https://www.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        "https://www.medicalnewstoday.com/rss",
        "https://www.healthline.com/rss",
    ],
    "World News": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    ],
}


async def get_user_category_preferences() -> Dict[str, int]:
    """Analyze user engagement to find favorite categories"""
    async with AsyncSessionLocal() as db:
        # Get view counts by category
        result = await db.execute(
            text(
                """
            SELECT t.category, COUNT(*) as views
            FROM content_view_history cvh
            JOIN content_items ci ON cvh.content_id = ci.id
            JOIN topics t ON ci.topic_id = t.id
            WHERE cvh.viewed_at > NOW() - INTERVAL '30 days'
            AND t.category IS NOT NULL
            AND t.category != 'General'
            GROUP BY t.category
            ORDER BY views DESC
        """
            )
        )

        preferences = {}
        rows = result.fetchall()

        for category, views in rows:
            preferences[category] = views

        return preferences


def _is_entry_recent(entry, week_ago: datetime) -> bool:
    """Check if entry is from the last 7 days"""
    if not (hasattr(entry, "published_parsed") and entry.published_parsed):
        return False
    
    try:
        time_tuple = entry.published_parsed[:6]
        if (time_tuple and len(time_tuple) >= 6 and 
            all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in time_tuple)):
            pub_date = datetime(
                int(time_tuple[0]), int(time_tuple[1]), int(time_tuple[2]),  # type: ignore
                int(time_tuple[3]), int(time_tuple[4]), int(time_tuple[5]),  # type: ignore
                tzinfo=timezone.utc
            )
            return pub_date > week_ago
    except (TypeError, ValueError, IndexError):
        pass
    return False

def _has_images(entry) -> bool:
    """Check if entry has images"""
    return (
        hasattr(entry, "media_content")
        or hasattr(entry, "media_thumbnail")
        or hasattr(entry, "enclosures")
    )

def _calculate_feed_score(total_items: int, recent_items: int, has_images: int) -> int:
    """Calculate quality score for feed"""
    score = 0
    if total_items >= 10:
        score += 30
    if recent_items >= 5:
        score += 40
    if has_images >= 5:
        score += 30
    return score

async def test_feed_quality(feed_url: str) -> Dict:
    """Test an RSS feed for quality metrics"""
    try:
        feed = await asyncio.to_thread(feedparser.parse, feed_url)
        
        if not feed.entries:
            return {"valid": False, "reason": "No entries found"}
        
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_items = sum(1 for entry in feed.entries[:10] if _is_entry_recent(entry, week_ago))
        has_images = sum(1 for entry in feed.entries[:10] if _has_images(entry))
        
        score = _calculate_feed_score(len(feed.entries), recent_items, has_images)
        
        return {
            "valid": True,
            "score": score,
            "total_items": len(feed.entries),
            "recent_items": recent_items,
            "items_with_images": has_images,
            "title": getattr(feed.feed, "title", "Unknown") if hasattr(feed, "feed") else "Unknown",
        }
    except Exception as e:
        return {"valid": False, "reason": str(e)}


async def discover_feeds_for_category(category: str, max_feeds: int = 3) -> List[Dict]:
    """Find and test new RSS feeds for a category"""
    print(f"\n🔍 Discovering feeds for {category}...")

    candidate_feeds = CANDIDATE_FEEDS.get(category, [])

    if not candidate_feeds:
        print(f"⚠️ No candidate feeds defined for {category}")
        return []

    tested_feeds = []

    for feed_url in candidate_feeds[: max_feeds * 2]:  # Test more than needed
        print(f"  Testing: {feed_url}")
        quality = await test_feed_quality(feed_url)

        if quality["valid"] and quality["score"] >= 60:
            tested_feeds.append(
                {
                    "url": feed_url,
                    "category": category,
                    "score": quality["score"],
                    "title": quality["title"],
                    "total_items": quality["total_items"],
                    "recent_items": quality["recent_items"],
                }
            )
            print(f"    ✅ Score: {quality['score']}/100 - {quality['title']}")
        else:
            reason = quality.get("reason", f"Low score: {quality.get('score', 0)}")
            print(f"    ❌ Rejected: {reason}")

        await asyncio.sleep(0.5)  # Be respectful

    # Sort by score and return top feeds
    tested_feeds.sort(key=lambda x: x["score"], reverse=True)
    return tested_feeds[:max_feeds]


async def get_current_feeds() -> Set[str]:
    """Get currently configured feeds from rss_feeds.txt"""
    feeds = set()
    try:
        async with aiofiles.open("rss_feeds.txt", "r", encoding="utf-8") as f:
            async for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 2:
                    feeds.add(parts[1])  # URL is second field
    except FileNotFoundError:
        print("⚠️ rss_feeds.txt not found, starting with empty feed list")
    except Exception as e:
        print(f"❌ Error reading rss_feeds.txt: {e}")

    return feeds


async def add_feed_to_config(feed_url: str, category: str, feed_name: str):
    """Add a new feed to the rss_feeds.txt file"""
    try:
        feed_key = feed_name.lower().replace(" ", "_").replace(".", "_")
        category_str = category if category else "None"

        # Append to rss_feeds.txt
        async with aiofiles.open("rss_feeds.txt", "a", encoding="utf-8") as f:
            await f.write(f"\n{feed_key}|{feed_url}|{category_str}|medium")

        print(f"✅ Added {feed_name} to rss_feeds.txt")
        return True
    except Exception as e:
        print(f"❌ Error adding feed to rss_feeds.txt: {e}")
        return False


async def main():
    print("🚀 Dynamic RSS Feed Discovery System")
    print("=" * 60)

    # Step 1: Analyze user preferences
    print("\n📊 Analyzing user category preferences...")
    preferences = await get_user_category_preferences()

    if not preferences:
        print("⚠️ No user activity found. Using default categories.")
        preferences = {"Sports": 100, "Technology": 80, "Entertainment": 60}

    print("\nTop categories by engagement:")
    for category, views in list(preferences.items())[:5]:
        print(f"  {category}: {views} views")

    # Step 2: Get current feeds
    current_feeds = await get_current_feeds()
    print(f"\n📡 Currently configured: {len(current_feeds)} feeds")

    # Step 3: Discover new feeds for top categories
    print("\n🔎 Discovering new RSS feeds...")

    new_feeds_added = 0
    for category, _ in list(preferences.items())[:3]:  # Top 3 categories
        discovered = await discover_feeds_for_category(category, max_feeds=2)

        for feed in discovered:
            if feed["url"] not in current_feeds:
                print(f"\n➕ Adding new feed: {feed['title']}")
                success = await add_feed_to_config(
                    feed["url"], feed["category"], feed["title"]
                )
                if success:
                    new_feeds_added += 1
                    current_feeds.add(feed["url"])

    print("\n✅ Discovery complete!")
    print(f"   Added {new_feeds_added} new feeds")
    print(f"   Total feeds now: {len(current_feeds) + new_feeds_added}")

    if new_feeds_added > 0:
        print("\n⚠️ Remember to:")
        print("   1. Review the changes in rss_feeds.txt")
        print("   2. Commit and push the changes")
        print("   3. Restart the service to activate new feeds")


if __name__ == "__main__":
    asyncio.run(main())
