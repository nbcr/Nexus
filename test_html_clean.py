#!/usr/bin/env python3
"""Test RSS HTML cleaning"""

import sys

sys.path.insert(0, ".")

from app.services.trending.rss_fetcher import RSSFetcher
from app.services.trending.categorization import ContentCategorizer

# Create instances
categorizer = ContentCategorizer()
rss_fetcher = RSSFetcher(categorizer)

# Test HTML description from BetaKit
raw_description = """<a href="https://betakit.com/canadas-ai-ambitions-with-minister-evan-solomon/" rel="nofollow" title="Canada's AI ambitions with Minister Evan Solomon"><img alt="AI Minister Evan Solomon at SAAS NORTH 2025." class="webfeedsFeaturedVisual wp-post-image" height="150" src="https://cdn.betakit.com/wp-content/uploads/2025/12/solomon_youtube_3-1-150x150.png" style="display: block; margin-bottom: 5px; clear: both;" width="150" /></a><p>Minister Evan Solomon sits down with C100 Executive Director Michael Buhr to discuss Canada's AI ambitions at SAAS NORTH 2025.</p>
<p>The post <a href="https://betakit.com/canadas-ai-ambitions-with-minister-evan-solomon/">Canada's AI ambitions with Minister Evan Solomon</a> appeared first on <a href="https://betakit.com">BetaKit</a>.</p>"""

print("Raw Description:")
print("=" * 70)
print(raw_description)
print("\n\nCleaned Description:")
print("=" * 70)
clean = rss_fetcher._clean_html_description(raw_description)
print(clean)
print(f"\n\nLength: {len(clean)} characters")
