#!/usr/bin/env python3
"""
Benchmark individual RSS feeds to determine optimal items per feed
Goal: Maximize total items fetched in under 15 minutes (900 seconds)
"""

import asyncio
import time
from typing import Dict, List
from app.services.trending.rss_fetcher import RSSFetcher
from app.services.trending.categorization import ContentCategorizer
from app.utils.async_rss_parser import get_async_rss_parser


async def benchmark_single_feed(
    fetcher: RSSFetcher,
    feed_name: str,
    feed_config: Dict,
    max_items: int = 10,
) -> Dict:
    """Benchmark a single feed with incrementally increasing items"""
    results = {}
    base_url = feed_config["url"]
    category_hint = feed_config.get("category_hint")

    print(f"\n📊 Benchmarking feed: {feed_name}")
    print(f"   URL: {base_url}")

    for items_count in range(1, max_items + 1):
        fetcher.items_per_feed = items_count

        try:
            start = time.time()
            feed = await asyncio.wait_for(
                get_async_rss_parser().parse_feed(base_url), timeout=10
            )
            elapsed = time.time() - start

            # Process entries
            items = fetcher._process_feed_entries(
                feed, base_url, category_hint, feed_name
            )

            result_time = time.time() - start

            results[items_count] = {
                "items_fetched": len(items),
                "parse_time": elapsed,
                "total_time": result_time,
                "success": True,
            }

            print(
                f"   {items_count} items: {result_time:.2f}s (parsed in {elapsed:.2f}s, got {len(items)} items)"
            )

        except asyncio.TimeoutError:
            results[items_count] = {"timeout": True, "success": False}
            print(f"   {items_count} items: ⏱️ TIMEOUT (10s)")
            break
        except Exception as e:
            results[items_count] = {"error": str(e), "success": False}
            print(f"   {items_count} items: ❌ ERROR: {e}")
            break

    return results


async def benchmark_all_feeds(max_items: int = 10, timeout_seconds: int = 900):
    """Benchmark all feeds to find optimal configuration"""
    categorizer = ContentCategorizer()
    fetcher = RSSFetcher(categorizer, items_per_feed=1, batch_size=1)

    total_start = time.time()
    feed_benchmarks = {}

    # Get list of feeds
    feeds_list = list(fetcher.rss_feeds.items())
    total_feeds = len(feeds_list)

    print(f"🚀 Starting benchmark of {total_feeds} feeds")
    print(f"⏱️  Target: Finish within {timeout_seconds}s (15 minutes)")
    print("=" * 70)

    for i, (feed_name, feed_config) in enumerate(feeds_list):
        elapsed_so_far = time.time() - total_start
        remaining_time = timeout_seconds - elapsed_so_far

        # Estimate if we have time for this feed
        if remaining_time < 30:
            print(
                f"\n⚠️ Running out of time! {remaining_time:.0f}s remaining. Stopping."
            )
            break

        print(
            f"\n[{i+1}/{total_feeds}] ({elapsed_so_far:.0f}s / {timeout_seconds}s) Time remaining: {remaining_time:.0f}s"
        )

        feed_benchmarks[feed_name] = await benchmark_single_feed(
            fetcher, feed_name, feed_config, max_items=max_items
        )

        # Check if we're running out of time
        elapsed_so_far = time.time() - total_start
        if elapsed_so_far > timeout_seconds * 0.8:  # Stop at 80% of budget
            print(f"\n⚠️ Approaching time limit. Benchmarked {i+1}/{total_feeds} feeds.")
            break

    total_elapsed = time.time() - total_start

    # Analyze results
    print("\n" + "=" * 70)
    print(f"✅ Benchmark completed in {total_elapsed:.1f}s")
    print("=" * 70)

    return feed_benchmarks, total_elapsed


def analyze_benchmarks(
    feed_benchmarks: Dict, total_time: float, target_time: int = 900
) -> Dict:
    """Analyze benchmark results to find optimal configuration"""
    print("\n📈 ANALYSIS")
    print("=" * 70)

    feed_capacities = {}

    for feed_name, results in feed_benchmarks.items():
        # Find max items before timeout/error
        max_safe_items = 0
        for items_count in sorted(results.keys()):
            if results[items_count]["success"]:
                max_safe_items = items_count
            else:
                break

        if max_safe_items > 0:
            feed_capacities[feed_name] = max_safe_items
            last_result = results[max_safe_items]
            print(
                f"{feed_name:40} | Max items: {max_safe_items} | Time: {last_result['total_time']:.2f}s"
            )
        else:
            print(f"{feed_name:40} | ❌ FAILED AT 1 ITEM")

    # Calculate total capacity
    total_items_available = sum(feed_capacities.values())
    avg_items_per_feed = (
        total_items_available / len(feed_capacities) if feed_capacities else 0
    )
    estimated_total_time = total_time * (
        avg_items_per_feed / 1
    )  # Extrapolate from 1 item baseline

    print("\n" + "=" * 70)
    print(f"Feeds benchmarked: {len(feed_capacities)} / {len(feed_benchmarks)}")
    print(f"Total item capacity: {total_items_available} items")
    print(f"Average items per feed: {avg_items_per_feed:.1f}")
    print(f"Estimated total fetch time: {estimated_total_time:.1f}s")
    print(f"Time budget: {target_time}s")

    if estimated_total_time < target_time:
        headroom = target_time - estimated_total_time
        print(f"✅ FEASIBLE - {headroom:.0f}s headroom")
    else:
        overage = estimated_total_time - target_time
        print(f"⚠️ EXCEEDS BUDGET by {overage:.0f}s")

    print("=" * 70)

    return feed_capacities


if __name__ == "__main__":
    print("RSS Feed Benchmarking Tool")
    print("This will test each feed to find optimal items per feed")
    print("Target: Complete all fetches within 15 minutes (900s)")
    print()

    # Run benchmark
    benchmarks, elapsed = asyncio.run(
        benchmark_all_feeds(max_items=10, timeout_seconds=900)
    )

    # Analyze
    capacities = analyze_benchmarks(benchmarks, elapsed, target_time=900)

    print("\n💾 Summary saved. Feed capacities:")
    for feed_name, max_items in sorted(capacities.items(), key=lambda x: -x[1]):
        print(f"  {feed_name:40} {max_items} items")
