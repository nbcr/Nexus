import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.trending_service import trending_service
from app.database import AsyncSessionLocal

async def test_trending_direct():
    print("🧪 Testing Google Trends Canada RSS integration directly...")
    
    # Test 1: Fetch trends from RSS
    print("\n1. 📡 Fetching trends from Google Trends RSS...")
    trends = await trending_service.fetch_canada_trends()
    
    if not trends:
        print("❌ No trends fetched - this might be due to:")
        print("   - Network connectivity issues")
        print("   - Google Trends RSS feed changes")
        print("   - Firewall restrictions")
        return
    
    print(f"✅ Successfully fetched {len(trends)} trends")
    print("Sample trends:")
    for i, trend in enumerate(trends[:5], 1):
        print(f"   {i}. {trend['title']}")
        print(f"      Category: {trend.get('category', 'N/A')}")
        print(f"      Description: {trend.get('description', 'N/A')[:100]}...")
    
    # Test 2: Save to database
    print("\n2. 💾 Testing database save...")
    async with AsyncSessionLocal() as db:
        saved_topics = await trending_service.save_trends_to_database(db)
        print(f"✅ Saved {len(saved_topics)} topics to database")
        
        if saved_topics:
            print("Sample saved topics:")
            for i, topic in enumerate(saved_topics[:3], 1):
                print(f"   {i}. {topic.title} (Score: {topic.trend_score})")

if __name__ == "__main__":
    asyncio.run(test_trending_direct())
