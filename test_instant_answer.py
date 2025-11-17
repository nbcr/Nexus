#!/usr/bin/env python3
"""
Test scraping instant answers from DuckDuckGo
"""
import asyncio
from app.services.article_scraper import article_scraper

async def test_instant_answer():
    """Test extracting instant answer from DuckDuckGo"""
    
    # Test with a person query (like khabib)
    test_url = "https://duckduckgo.com/?q=khabib+nurmagomedov&ia=web"
    
    print(f"🔍 Testing instant answer extraction...")
    print(f"URL: {test_url}\n")
    
    result = await article_scraper.fetch_search_context(test_url)
    
    if result:
        print("✅ Scraping succeeded!\n")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Domain: {result.get('domain', 'N/A')}")
        print(f"Instant Answer: {bool(result.get('instant_answer'))}")
        print(f"Search Results: {len(result.get('search_results', []))} items")
        print(f"\nContent length: {len(result.get('content', ''))} chars")
        print("\n" + "="*60)
        print("CONTENT:")
        print("="*60)
        print(result.get('content', 'N/A'))
    else:
        print("❌ Scraping failed - returned None")

if __name__ == "__main__":
    asyncio.run(test_instant_answer())
