#!/usr/bin/env python3
"""
Update PyTrends items to use DuckDuckGo search URLs instead of news article URLs
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ContentItem, Topic


async def fix_pytrends_urls():
    """Update PyTrends items to have search URLs"""
    async with AsyncSessionLocal() as db:
        # Get all PyTrends items
        result = await db.execute(
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(ContentItem.content_type == "trending_analysis")
        )

        items = result.all()

        print(f"Found {len(items)} PyTrends items to fix\n")

        fixed_count = 0
        for content, topic in items:
            # Check if it's already a search URL
            current_url = content.source_urls[0] if content.source_urls else None
            if current_url and (
                "duckduckgo.com" in current_url or "google.com/search" in current_url
            ):
                continue

            # Create DuckDuckGo search URL from topic title
            search_query = topic.title.replace(" ", "+")
            new_url = f"https://duckduckgo.com/?q={search_query}&ia=web"

            # Update the content item
            content.source_urls = [new_url]

            print(f"✓ Fixed ID {content.id}: {topic.title}")
            print(f"  Old URL: {current_url}")
            print(f"  New URL: {new_url}\n")

            fixed_count += 1

        if fixed_count > 0:
            await db.commit()
            print(f"✅ Fixed {fixed_count} PyTrends items!")
        else:
            print("✅ All PyTrends items already have search URLs!")


if __name__ == "__main__":
    asyncio.run(fix_pytrends_urls())
