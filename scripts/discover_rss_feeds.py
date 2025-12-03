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
from datetime import datetime, timedelta
from typing import List, Dict, Set
import feedparser
import aiohttp
from sqlalchemy import text, func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal


# RSS Feed Discovery Sources
FEED_DISCOVERY_APIS = {
    'feedly': 'https://feedly.com/v3/search/feeds?query={}',  # Free API
    'feedspot': None,  # Requires scraping
}

# Curated feed database by category
CANDIDATE_FEEDS = {
    'Sports': [
        'https://www.espn.com/espn/rss/news',
        'https://sports.yahoo.com/mlb/rss.xml',
        'https://www.sportsnet.ca/feed/',
        'https://www.si.com/rss/si_topstories.rss',
        'https://www.cbssports.com/rss/headlines',
        'https://www.theringer.com/rss/index.xml',
    ],
    'Technology': [
        'https://techcrunch.com/feed/',
        'https://www.theverge.com/rss/index.xml',
        'https://arstechnica.com/feed/',
        'https://www.wired.com/feed/rss',
        'https://www.engadget.com/rss.xml',
        'https://hacks.mozilla.org/feed/',
        'https://blog.google/rss/',
    ],
    'Entertainment': [
        'https://variety.com/feed/',
        'https://www.hollywoodreporter.com/feed/',
        'https://ew.com/feed/',
        'https://www.rollingstone.com/feed/',
        'https://pitchfork.com/rss/reviews/albums/',
        'https://www.billboard.com/feed/',
    ],
    'Business': [
        'https://www.bloomberg.com/feed/podcast/bloomberg-businessweek',
        'https://www.wsj.com/xml/rss/3_7014.xml',
        'https://www.businessinsider.com/rss',
        'https://www.forbes.com/real-time/feed2/',
        'https://www.cnbc.com/id/100003114/device/rss/rss.html',
    ],
    'Science': [
        'https://www.nature.com/nature.rss',
        'https://www.sciencedaily.com/rss/all.xml',
        'https://www.newscientist.com/feed/home',
        'https://www.scientificamerican.com/feed/',
        'https://www.space.com/feeds/all',
    ],
    'Health': [
        'https://www.health.com/rss',
        'https://www.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC',
        'https://www.medicalnewstoday.com/rss',
        'https://www.healthline.com/rss',
    ],
    'World News': [
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://www.aljazeera.com/xml/rss/all.xml',
        'https://www.theguardian.com/world/rss',
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    ],
}


async def get_user_category_preferences() -> Dict[str, int]:
    """Analyze user engagement to find favorite categories"""
    async with AsyncSessionLocal() as db:
        # Get view counts by category
        result = await db.execute(text("""
            SELECT t.category, COUNT(*) as views
            FROM content_view_history cvh
            JOIN content_items ci ON cvh.content_id = ci.id
            JOIN topics t ON ci.topic_id = t.id
            WHERE cvh.viewed_at > NOW() - INTERVAL '30 days'
            AND t.category IS NOT NULL
            AND t.category != 'General'
            GROUP BY t.category
            ORDER BY views DESC
        """))
        
        preferences = {}
        rows = result.fetchall()
        
        for category, views in rows:
            preferences[category] = views
        
        return preferences


async def test_feed_quality(feed_url: str) -> Dict:
    """Test an RSS feed for quality metrics"""
    try:
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            return {'valid': False, 'reason': 'No entries found'}
        
        # Check freshness - at least one item from last 7 days
        recent_items = 0
        has_images = 0
        week_ago = datetime.now() - timedelta(days=7)
        
        for entry in feed.entries[:10]:
            # Check if recent
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date > week_ago:
                    recent_items += 1
            
            # Check for images
            if (hasattr(entry, 'media_content') or 
                hasattr(entry, 'media_thumbnail') or
                hasattr(entry, 'enclosures')):
                has_images += 1
        
        score = 0
        if len(feed.entries) >= 10:
            score += 30
        if recent_items >= 5:
            score += 40
        if has_images >= 5:
            score += 30
        
        return {
            'valid': True,
            'score': score,
            'total_items': len(feed.entries),
            'recent_items': recent_items,
            'items_with_images': has_images,
            'title': feed.feed.get('title', 'Unknown'),
        }
    except Exception as e:
        return {'valid': False, 'reason': str(e)}


async def discover_feeds_for_category(category: str, max_feeds: int = 3) -> List[Dict]:
    """Find and test new RSS feeds for a category"""
    print(f"\n🔍 Discovering feeds for {category}...")
    
    candidate_feeds = CANDIDATE_FEEDS.get(category, [])
    
    if not candidate_feeds:
        print(f"⚠️ No candidate feeds defined for {category}")
        return []
    
    tested_feeds = []
    
    for feed_url in candidate_feeds[:max_feeds * 2]:  # Test more than needed
        print(f"  Testing: {feed_url}")
        quality = await test_feed_quality(feed_url)
        
        if quality['valid'] and quality['score'] >= 60:
            tested_feeds.append({
                'url': feed_url,
                'category': category,
                'score': quality['score'],
                'title': quality['title'],
                'total_items': quality['total_items'],
                'recent_items': quality['recent_items']
            })
            print(f"    ✅ Score: {quality['score']}/100 - {quality['title']}")
        else:
            reason = quality.get('reason', f"Low score: {quality.get('score', 0)}")
            print(f"    ❌ Rejected: {reason}")
        
        await asyncio.sleep(0.5)  # Be respectful
    
    # Sort by score and return top feeds
    tested_feeds.sort(key=lambda x: x['score'], reverse=True)
    return tested_feeds[:max_feeds]


async def get_current_feeds() -> Set[str]:
    """Get currently configured feeds from trending_service.py"""
    try:
        with open('app/services/trending_service.py', 'r') as f:
            content = f.read()
            
        # Extract URLs from the file
        import re
        urls = re.findall(r"'url':\s*'([^']+)'", content)
        return set(urls)
    except Exception as e:
        print(f"Error reading current feeds: {e}")
        return set()


async def add_feed_to_config(feed_url: str, category: str, feed_name: str):
    """Add a new feed to the trending_service.py configuration"""
    try:
        with open('app/services/trending_service.py', 'r') as f:
            content = f.read()
        
        # Find the self.rss_feeds dictionary
        import re
        pattern = r"(self\.rss_feeds = \{[^}]+)(\s+\})"
        
        # Create new feed entry
        feed_key = feed_name.lower().replace(' ', '_').replace('.', '_')
        new_feed = f"""            '{feed_key}': {{
                'url': '{feed_url}',
                'category_hint': '{category}',
                'priority': 'medium'
            }},"""
        
        # Insert before the closing brace
        updated = re.sub(pattern, r"\1" + new_feed + r"\2", content)
        
        with open('app/services/trending_service.py', 'w') as f:
            f.write(updated)
        
        print(f"✅ Added {feed_name} to configuration")
        return True
    except Exception as e:
        print(f"❌ Error adding feed to config: {e}")
        return False


async def main():
    print("🚀 Dynamic RSS Feed Discovery System")
    print("=" * 60)
    
    # Step 1: Analyze user preferences
    print("\n📊 Analyzing user category preferences...")
    preferences = await get_user_category_preferences()
    
    if not preferences:
        print("⚠️ No user activity found. Using default categories.")
        preferences = {'Sports': 100, 'Technology': 80, 'Entertainment': 60}
    
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
            if feed['url'] not in current_feeds:
                print(f"\n➕ Adding new feed: {feed['title']}")
                success = await add_feed_to_config(
                    feed['url'],
                    feed['category'],
                    feed['title']
                )
                if success:
                    new_feeds_added += 1
                    current_feeds.add(feed['url'])
    
    print(f"\n✅ Discovery complete!")
    print(f"   Added {new_feeds_added} new feeds")
    print(f"   Total feeds now: {len(current_feeds) + new_feeds_added}")
    
    if new_feeds_added > 0:
        print("\n⚠️ Remember to:")
        print("   1. Review the changes in app/services/trending_service.py")
        print("   2. Commit and push the changes")
        print("   3. Restart the service to activate new feeds")


if __name__ == "__main__":
    asyncio.run(main())
