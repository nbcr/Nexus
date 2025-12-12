#!/usr/bin/env python3
"""
Fetch items from RSS feeds and add to database
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio
import re
import aiofiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.models import ContentItem, Topic
from app.utils.async_rss_parser import AsyncRSSParser

# Use sync connection
DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL_SYNC environment variable not set")

def generate_slug(title):
    """Generate URL-safe slug from title"""
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower())
    return slug.strip('-')[:50]

async def read_first_feed(feeds_file):
    """Read first valid feed from feeds file"""
    async with aiofiles.open(feeds_file, 'r') as f:
        async for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            if len(parts) >= 2:
                return parts[0], parts[1]
    return None, None

def get_or_create_topic(session, feed_name):
    """Get existing topic or create new one"""
    topic = session.query(Topic).filter_by(title=feed_name).first()
    if not topic:
        topic = Topic(
            title=feed_name,
            normalized_title=feed_name.lower().replace(' ', '_'),
            description=f"Feed: {feed_name}",
            trend_score=0.5,
            category="News",
            tags=[feed_name]
        )
        session.add(topic)
        session.commit()
        print(f"Created topic: {feed_name}")
    return topic

def create_content_item(item, topic_id, feed_name):
    """Create content item from RSS item"""
    link = item.get('link', '')
    title = item.get('title', 'No title')
    
    if not link or not title:
        return None
    
    return ContentItem(
        topic_id=topic_id,
        title=title,
        slug=generate_slug(title),
        description=item.get('description', ''),
        source_urls=[link],
        source_metadata={
            'feed': feed_name,
            'author': item.get('author', ''),
            'published': str(item.get('published', ''))
        }
    )

async def fetch_and_add_items():
    """Fetch items from first RSS feed and add to database"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL_SYNC environment variable not set")
    
    engine = create_engine(DATABASE_URL, echo=False)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    
    try:
        feeds_file = Path(__file__).parent / "rss_feeds.txt"
        if not feeds_file.exists():
            print(f"RSS feeds file not found: {feeds_file}")
            return
        
        feed_name, feed_url = await read_first_feed(feeds_file)
        if not feed_url or not feed_name:
            print("No RSS feeds found")
            return
        
        print(f"Fetching from: {feed_name}")
        print(f"URL: {feed_url}")
        
        parser = AsyncRSSParser()
        feed_data = await parser.parse_feed(feed_url)
        items = feed_data.get('entries', [])
        
        if not items:
            print("No items found in feed")
            return
        
        topic = get_or_create_topic(session, feed_name)
        
        added = 0
        for item in items[:5]:
            content = create_content_item(item, topic.id, feed_name)
            if content:
                session.add(content)
                added += 1
        
        session.commit()
        print(f"✅ Added {added} items to database")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    asyncio.run(fetch_and_add_items())
