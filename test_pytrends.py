"""
Test PyTrends integration

This script tests the PyTrends service to ensure it's fetching
trending topics and related content correctly.
"""
import asyncio
from app.services.pytrends_service import pytrends_service


async def test_pytrends():
    print("=" * 60)
    print("Testing PyTrends Service")
    print("=" * 60)
    
    # Test 1: Fetch trending searches
    print("\n📊 Test 1: Fetching trending searches...")
    print("-" * 60)
    trending = await pytrends_service.fetch_trending_searches()
    print(f"\nFound {len(trending)} trending searches:")
    for i, trend in enumerate(trending[:5], 1):
        print(f"  {i}. {trend['title']} (score: {trend['trend_score']:.2f})")
    
    # Test 2: Fetch related topics for first trending search
    if trending:
        keyword = trending[0]['title']
        print(f"\n🔍 Test 2: Fetching related topics for '{keyword}'...")
        print("-" * 60)
        related_topics = await pytrends_service.fetch_related_topics(keyword, timeframe='now 1-d')
        print(f"\nFound {len(related_topics)} related topics:")
        for i, topic in enumerate(related_topics[:5], 1):
            print(f"  {i}. {topic['title']} (score: {topic['trend_score']:.2f})")
        
        # Test 3: Fetch related queries
        print(f"\n❓ Test 3: Fetching related queries for '{keyword}'...")
        print("-" * 60)
        related_queries = await pytrends_service.fetch_related_queries(keyword, timeframe='now 1-d')
        print(f"\nFound {len(related_queries)} related queries:")
        for i, query in enumerate(related_queries[:5], 1):
            print(f"  {i}. {query['title']} (score: {query['trend_score']:.2f})")
        
        # Test 4: Fetch interest over time
        print(f"\n📈 Test 4: Fetching interest over time for '{keyword}'...")
        print("-" * 60)
        interest = await pytrends_service.fetch_interest_over_time([keyword], timeframe='now 7-d')
        print(f"\nInterest data points: {len(interest.get('data', []))}")
        if interest.get('peak_dates'):
            print("Peak interest dates:")
            for kw, date in interest['peak_dates'].items():
                print(f"  - {kw}: {date}")
    
    # Test 5: Test enrichment with sample trends
    print("\n🎨 Test 5: Testing trend enrichment...")
    print("-" * 60)
    sample_trends = [
        {
            'title': 'AI Technology',
            'original_query': 'AI Technology',
            'trend_score': 0.9
        }
    ]
    enriched = await pytrends_service.enrich_trends_with_pytrends(sample_trends, max_topics=1)
    print(f"Original trends: {len(sample_trends)}")
    print(f"Enriched trends: {len(enriched)}")
    print("\nEnriched trend titles:")
    for i, trend in enumerate(enriched[:10], 1):
        print(f"  {i}. {trend['title']} (source: {trend.get('source', 'Unknown')})")
    
    print("\n" + "=" * 60)
    print("✅ PyTrends testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_pytrends())
