#!/usr/bin/env python3
"""Test BetaKit RSS feed and article scraping"""

import feedparser
import sys

sys.path.insert(0, ".")

from app.services.article_scraper import article_scraper

# Fetch BetaKit RSS
print("Fetching BetaKit RSS feed...")
feed = feedparser.parse("https://betakit.com/feed/")

print(f"\nFeed Title: {feed.feed.get('title', 'N/A')}")
print(f"Total Entries: {len(feed.entries)}\n")

if feed.entries:
    # Get the first article
    entry = feed.entries[0]
    print("=" * 70)
    print(f"Article Title: {entry.title}")
    print(f"Link: {entry.link}")
    print(f"Published: {entry.get('published', 'N/A')}")

    if hasattr(entry, "summary"):
        print(f"\nRSS Summary Length: {len(entry.summary)} characters")
        print(f"RSS Summary Preview:\n{entry.summary[:500]}...")

    # Now scrape the actual article
    print("\n" + "=" * 70)
    print("Attempting to scrape article content...")
    print("=" * 70)

    article_data = article_scraper.fetch_article(entry.link)

    if article_data:
        print("\n✅ Scraping Result:")
        print(f"Title: {article_data.get('title', 'N/A')}")
        print(f"Author: {article_data.get('author', 'N/A')}")
        print(f"Image URL: {article_data.get('image_url', 'N/A')}")
        print(f"Content Length: {len(article_data.get('content', ''))} characters")
        print("\nExtracted Content Preview:")
        print("-" * 70)
        print(article_data.get("content", "No content")[:800])
        print("-" * 70)
    else:
        print("\n❌ Failed to scrape article")
else:
    print("No entries found in feed")
