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

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.models import ContentItem, Topic
from app.utils.async_rss_parser import AsyncRSSParser

# Use sync connection
DATABASE_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:***REMOVED***@localhost:5432/nexus")

async def fetch_and_add_items():
    """Fetch items from first RSS feed and add to database"""
    
    def generate_slug(title):
        """Generate URL-safe slug from title"""
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())
        return slug.strip('-')[:50]
    
    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Read RSS feeds file
        feeds_file = Path(__file__).parent / "rss_feeds.txt"
        if not feeds_file.exists():
            print(f"RSS feeds file not found: {feeds_file}")
            return
        
        # Get first feed
        feed_url = None
        feed_name = None
        with open(feeds_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('|')
                if len(parts) >= 2:
                    feed_name = parts[0]
                    feed_url = parts[1]
                    break
        
        if not feed_url or not feed_name:
            print("No RSS feeds found")
            return
        
        print(f"Fetching from: {feed_name}")
        print(f"URL: {feed_url}")
        
        # Parse RSS feed
        parser = AsyncRSSParser()
        feed_data = await parser.parse_feed(feed_url)
        items = feed_data.get('entries', [])
        
        if not items:
            print("No items found in feed")
            return
        
        # Get or create topic for this feed
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
        
        # Add items
        added = 0
        for item in items[:5]:  # Add first 5 items
            link = item.get('link', '')
            title = item.get('title', 'No title')
            
            if not link or not title:
                continue
            
            content = ContentItem(
                topic_id=topic.id,
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
