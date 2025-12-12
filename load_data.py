#!/usr/bin/env python3
"""
Load initial database with RSS feeds and categories
"""
import os
import sys
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.db import Base
from app.models import Topic

# Use sync connection from environment
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL_SYNC")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL_SYNC not found in .env file")


def load_feeds():
    """Load RSS feeds from rss_feeds.txt"""
    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Read RSS feeds file
        feeds_file = Path(__file__).parent / "rss_feeds.txt"
        if not feeds_file.exists():
            print(f"RSS feeds file not found: {feeds_file}")
            return

        categories = {}
        with open(feeds_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("|")
                if len(parts) >= 3:
                    category = parts[2]

                    if category not in categories:
                        categories[category] = {"name": category, "count": 0}
                    categories[category]["count"] += 1

        # Check if topics already exist
        existing = session.query(Topic).count()
        if existing > 0:
            print(f"✅ Database already has {existing} topics")
            return

        # Create topic for each category
        print(f"Creating {len(categories)} category topics...")
        for cat_name, cat_info in categories.items():
            topic = Topic(
                title=cat_name,
                normalized_title=cat_name.lower().replace(" ", "_"),
                description=f"News and content in {cat_name}",
                trend_score=0.5,
                category=cat_name,
                tags=[cat_name],
            )
            session.add(topic)

        session.commit()
        print(f"✅ Created {len(categories)} category topics")

    except Exception as e:
        print(f"❌ Error loading feeds: {e}")
        session.rollback()
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    load_feeds()
