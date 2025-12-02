#!/usr/bin/env python3
"""
Test specific search queries that are failing
"""
import asyncio
from app.services.article_scraper import article_scraper


async def test_queries():
    """Test the failing queries"""

    test_queries = [
        "craig jones vs gordon ryan",
        "jon jones reach",
    ]

    for query in test_queries:
        url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=web"
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print(f"URL: {url}")
        print("=" * 60)

        result = await article_scraper.fetch_search_context(url)

        if result:
            print(f"✅ Success!")
            print(f"Title: {result.get('title')}")
            print(f"Has instant answer: {bool(result.get('instant_answer'))}")
            print(f"Content length: {len(result.get('content', ''))}")
            print(f"\nContent preview:")
            print(result.get("content", "N/A")[:300])
        else:
            print("❌ Failed - returned None")


if __name__ == "__main__":
    asyncio.run(test_queries())
