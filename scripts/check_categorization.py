#!/usr/bin/env python3
"""
Category Quality Checker
Uses free AI APIs to validate content categorization and suggest improvements.

Free AI API options:
1. Groq (free tier: 14,400 requests/day) - Fast, reliable
2. Together AI (free tier: good limits)
3. OpenRouter (free models available)
4. Hugging Face Inference API (free for many models)

Run: python scripts/check_categorization.py
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal


# Groq API is free and fast - get key at https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Alternative: Together AI - get key at https://api.together.xyz
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

# Rate limiting
RATE_LIMIT_FILE = Path("/tmp/nexus_ai_requests.json")
DAILY_LIMIT = 14000  # Stay under 14,400 Groq limit
HOURLY_LIMIT = 600  # ~14,400 / 24

def load_request_counts():
    """Load request counts from file"""
    if not RATE_LIMIT_FILE.exists():
        return {"daily": {}, "hourly": {}}
    
    try:
        with open(RATE_LIMIT_FILE, 'r') as f:
            data = json.load(f)
            # Clean old data
            today = datetime.now().strftime("%Y-%m-%d")
            current_hour = datetime.now().strftime("%Y-%m-%d-%H")
            
            # Keep only today's daily count
            if today not in data.get("daily", {}):
                data["daily"] = {today: 0}
            else:
                data["daily"] = {today: data["daily"][today]}
            
            # Keep only current hour
            if current_hour not in data.get("hourly", {}):
                data["hourly"] = {current_hour: 0}
            else:
                data["hourly"] = {current_hour: data["hourly"][current_hour]}
            
            return data
    except:
        return {"daily": {}, "hourly": {}}


def save_request_counts(counts):
    """Save request counts to file"""
    with open(RATE_LIMIT_FILE, 'w') as f:
        json.dump(counts, f)


def check_rate_limit():
    """Check if we're within rate limits"""
    counts = load_request_counts()
    today = datetime.now().strftime("%Y-%m-%d")
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    
    daily_count = counts["daily"].get(today, 0)
    hourly_count = counts["hourly"].get(current_hour, 0)
    
    if daily_count >= DAILY_LIMIT:
        print(f"⚠️ Daily limit reached: {daily_count}/{DAILY_LIMIT}")
        return False
    
    if hourly_count >= HOURLY_LIMIT:
        print(f"⚠️ Hourly limit reached: {hourly_count}/{HOURLY_LIMIT}")
        return False
    
    return True


def increment_request_count():
    """Increment request counters"""
    counts = load_request_counts()
    today = datetime.now().strftime("%Y-%m-%d")
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    
    counts["daily"][today] = counts["daily"].get(today, 0) + 1
    counts["hourly"][current_hour] = counts["hourly"].get(current_hour, 0) + 1
    
    save_request_counts(counts)


async def check_with_groq(title: str, description: str) -> dict:
    """Check categorization using Groq API (free tier)"""
    import aiohttp
    
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not set"}
    
    # Check rate limit before making request
    if not check_rate_limit():
        return {"error": "Rate limit reached"}
    
    categories = [
        "Sports", "Entertainment", "Technology", "Business", "Politics",
        "Health", "Science", "World News", "Crime", "Weather",
        "Education", "Lifestyle", "General"
    ]
    
    prompt = f"""Categorize this news story into ONE of these categories: {', '.join(categories)}

Title: {title}
Description: {description}

Reply with ONLY the category name, nothing else."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",  # Fast and accurate
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 20
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"error": f"API error {resp.status}: {text}"}
                
                data = await resp.json()
                suggested = data["choices"][0]["message"]["content"].strip()
                
                # Increment counter after successful request
                increment_request_count()
                
                return {
                    "suggested_category": suggested,
                    "model": "groq/llama-3.3-70b"
                }
    except Exception as e:
        return {"error": str(e)}


async def check_with_together(title: str, description: str) -> dict:
    """Check categorization using Together AI (free tier)"""
    import aiohttp
    
    if not TOGETHER_API_KEY:
        return {"error": "TOGETHER_API_KEY not set"}
    
    categories = [
        "Sports", "Entertainment", "Technology", "Business", "Politics",
        "Health", "Science", "World News", "Crime", "Weather",
        "Education", "Lifestyle", "General"
    ]
    
    prompt = f"""Categorize this news story into ONE of these categories: {', '.join(categories)}

Title: {title}
Description: {description}

Reply with ONLY the category name."""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TOGETHER_API_URL,
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 20
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return {"error": f"API error {resp.status}: {text}"}
                
                data = await resp.json()
                suggested = data["choices"][0]["message"]["content"].strip()
                
                return {
                    "suggested_category": suggested,
                    "model": "together/llama-3.1-8b"
                }
    except Exception as e:
        return {"error": str(e)}


async def check_recent_categorization(hours: int = 24, limit: int = 20):
    """Check recent content categorization quality"""
    print(f"\n🔍 Checking categorization for content from last {hours} hours...\n")
    
    # Show current rate limit status
    counts = load_request_counts()
    today = datetime.now().strftime("%Y-%m-%d")
    current_hour = datetime.now().strftime("%Y-%m-%d-%H")
    daily_count = counts["daily"].get(today, 0)
    hourly_count = counts["hourly"].get(current_hour, 0)
    print(f"📊 Rate limit status: {daily_count}/{DAILY_LIMIT} daily, {hourly_count}/{HOURLY_LIMIT} hourly\n")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(text(f"""
            SELECT ci.id, ci.title, t.category, t.description, ci.created_at
            FROM content_items ci
            JOIN topics t ON ci.topic_id = t.id
            WHERE ci.is_published = true
            AND ci.created_at > NOW() - INTERVAL '{hours} HOURS'
            ORDER BY ci.created_at DESC
            LIMIT {limit}
        """))
        
        items = result.fetchall()
        
        if not items:
            print("No recent content found.")
            return
        
        print(f"Found {len(items)} items to check\n")
        
        mismatches = []
        
        for id, title, category, description, created_at in items:
            desc = description or ""
            
            # Try Groq first (faster), fallback to Together
            if GROQ_API_KEY:
                ai_result = await check_with_groq(title, desc)
            elif TOGETHER_API_KEY:
                ai_result = await check_with_together(title, desc)
            else:
                print("❌ No API key configured. Set GROQ_API_KEY or TOGETHER_API_KEY environment variable.")
                print("\nGet free API keys:")
                print("  - Groq: https://console.groq.com (14,400 requests/day)")
                print("  - Together AI: https://api.together.xyz")
                return
            
            if "error" in ai_result:
                print(f"⚠️ Error checking [{id}]: {ai_result['error']}")
                continue
            
            suggested = ai_result["suggested_category"]
            model = ai_result.get("model", "unknown")
            
            if suggested != category:
                mismatches.append({
                    "id": id,
                    "title": title,
                    "current": category,
                    "suggested": suggested,
                    "created": created_at
                })
                print(f"❌ MISMATCH [{id}]")
                print(f"   Title: {title[:80]}")
                print(f"   Current: {category}")
                print(f"   AI Suggested ({model}): {suggested}")
                print()
            else:
                print(f"✅ [{id}] {category} - {title[:60]}")
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.1)
        
        print(f"\n📊 Summary:")
        print(f"   Total checked: {len(items)}")
        print(f"   Mismatches: {len(mismatches)}")
        print(f"   Accuracy: {((len(items) - len(mismatches)) / len(items) * 100):.1f}%")
        
        if mismatches:
            print(f"\n⚠️ Items that may need recategorization:")
            for item in mismatches:
                print(f"   UPDATE topics SET category = '{item['suggested']}' WHERE id = (SELECT topic_id FROM content_items WHERE id = {item['id']});")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check content categorization quality using AI")
    parser.add_argument("--hours", type=int, default=24, help="Check content from last N hours")
    parser.add_argument("--limit", type=int, default=20, help="Max number of items to check")
    
    args = parser.parse_args()
    
    await check_recent_categorization(hours=args.hours, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
