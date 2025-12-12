"""
Performance testing script for RSS fetching
Tests different item limits per feed and measures execution time
"""

import asyncio
import time
import sys
from app.services.trending import trending_service
from app.db import AsyncSessionLocal


async def test_fetch_with_limit(
    items_per_feed: int, timeout_seconds: int = 40
) -> tuple:
    """
    Test RSS fetching with a specific items per feed limit
    Returns (items_per_feed, total_time, success)
    """
    # Temporarily patch the limit
    original_limit = 1

    # Find and patch the limit in rss_fetcher
    fetcher = trending_service.rss_fetcher

    print(f"\n{'='*60}")
    print(f"Testing with {items_per_feed} items per feed")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        async with asyncio.timeout(timeout_seconds):
            topics, new_items = await trending_service.save_trends_to_database(
                AsyncSessionLocal()
            )
            elapsed = time.time() - start_time
            print(f"\n✅ Completed in {elapsed:.2f}s")
            print(f"   Topics: {len(topics)}, New items: {new_items}")
            return items_per_feed, elapsed, True
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        print(f"\n⏱️ Timeout after {elapsed:.2f}s (limit: {timeout_seconds}s)")
        return items_per_feed, elapsed, False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Error after {elapsed:.2f}s: {e}")
        return items_per_feed, elapsed, False


async def run_performance_test():
    """Run incremental performance test"""
    print("🚀 RSS Fetch Performance Test")
    print("Incrementally increasing items per feed until we exceed 30s\n")

    results = []
    items_limit = 1
    max_limit = 20
    target_time = 30

    while items_limit <= max_limit:
        # Patch the fetcher
        original_code = trending_service.rss_fetcher._process_feed_entries

        def patched_process(feed, feed_url, category_hint=None, source_name="RSS", limit=items_limit):
            """Patched version that respects items_limit"""
            trends = []
            is_google_trends = "trends.google.com" in feed_url

            for entry in feed.get("entries", [])[:limit]:
                trend_data = trending_service.rss_fetcher._process_single_entry(
                    entry, is_google_trends, feed_url, category_hint, source_name
                )
                if trend_data:
                    trends.append(trend_data)

            return trends

        trending_service.rss_fetcher._process_feed_entries = patched_process

        items_per_feed, elapsed, success = await test_fetch_with_limit(items_limit)
        results.append((items_per_feed, elapsed, success))

        # Restore
        trending_service.rss_fetcher._process_feed_entries = original_code

        if elapsed > target_time:
            print(f"\n⚠️ Exceeded {target_time}s target!")
            break

        items_limit += 1

    # Print summary
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"{'Items/Feed':<15} {'Time (s)':<15} {'Status':<15}")
    print("-" * 60)

    for items, elapsed, success in results:
        status = "✅ OK" if success else "⏱️ Timeout"
        if elapsed > target_time:
            status = "⚠️ SLOW"
        print(f"{items:<15} {elapsed:<15.2f} {status:<15}")

    # Recommendation
    if results:
        safe_limit = None
        for items, elapsed, success in results:
            if elapsed <= target_time:
                safe_limit = items

        print("\n📊 RECOMMENDATION:")
        if safe_limit:
            print(
                f"   Safe limit: {safe_limit} items/feed ({results[safe_limit-1][1]:.2f}s)"
            )
            print(
                f"   Estimated total items: {safe_limit * len(trending_service.rss_fetcher.rss_feeds)}"
            )
        else:
            print("   Even 1 item/feed is too slow!")


if __name__ == "__main__":
    asyncio.run(run_performance_test())
