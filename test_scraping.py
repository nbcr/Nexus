#!/usr/bin/env python3
"""
Test script to check if scraping is working for PyTrends items
"""
import asyncio
import sys
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ContentItem
from app.services.article_scraper import article_scraper


async def test_scraping():
    """Test scraping a PyTrends item"""
    async with AsyncSessionLocal() as db:
        # Get a recent PyTrends item
        result = await db.execute(
            select(ContentItem)
            .where(ContentItem.content_type == "trending_analysis")
            .order_by(ContentItem.created_at.desc())
            .limit(1)
        )

        item = result.scalar_one_or_none()

        if not item:
            print("❌ No PyTrends items found in database")
            return

        print(f"📋 Testing scraping for content_id: {item.id}")
        print(f"   Title: {item.title}")
        print(f"   Source URL: {item.source_urls[0] if item.source_urls else 'None'}")
        print()

        if not item.source_urls:
            print("❌ No source URL available")
            return

        # Try to scrape
        print("🔍 Attempting to scrape...")
        article_data = await article_scraper.fetch_search_context(item.source_urls[0])

        if article_data:
            print("✅ Scraping succeeded!")
            print(f"   Title: {article_data.get('title', 'N/A')}")
            print(f"   Content length: {len(article_data.get('content', ''))} chars")
            print(
                f"   Search results: {len(article_data.get('search_results', []))} items"
            )
            print()
            print("📄 Content preview:")
            print(article_data.get("content", "N/A")[:500])
        else:
            print("❌ Scraping failed - returned None")


if __name__ == "__main__":
    asyncio.run(test_scraping())
