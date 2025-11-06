import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.trending_service import trending_service
from app.database import AsyncSessionLocal

async def test_trending_system():
    print("Testing Google Trends Canada RSS integration...")
    
    # Test 1: Fetch trends directly
    print("\n1. Testing RSS feed fetch...")
    trends = await trending_service.fetch_canada_trends()
    print(f"✅ Fetched {len(trends)} trends")
    for i, trend in enumerate(trends[:3], 1):
        print(f"   {i}. {trend['title']}")
    
    # Test 2: Save to database
    print("\n2. Testing database save...")
    async with AsyncSessionLocal() as db:
        saved_topics = await trending_service.save_trends_to_database(db)
        print(f"✅ Saved {len(saved_topics)} topics to database")
    
    # Test 3: Test API endpoint
    print("\n3. Testing API endpoint...")
    import requests
    response = requests.get("http://localhost:8000/api/v1/trending/test-feed")
    print(f"✅ API test: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_trending_system())
