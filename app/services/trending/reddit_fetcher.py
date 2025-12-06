"""Reddit trending content fetching"""

import asyncio
import requests
from datetime import datetime
from typing import List, Dict


class RedditFetcher:
    """Fetches trending posts from Reddit"""

    def __init__(self):
        self.enabled = True
        self.subreddits = [
            ("all", "Popular"),
            ("worldnews", "World News"),
            ("news", "News"),
            ("technology", "Technology"),
            ("science", "Science"),
            ("sports", "Sports"),
            ("entertainment", "Entertainment"),
            ("todayilearned", "TIL"),
            ("explainlikeimfive", "ELI5"),
            ("askreddit", "AskReddit"),
        ]

    async def fetch_reddit_trends(self) -> List[Dict]:
        """Fetch trending posts from popular subreddits using Reddit JSON API"""
        # DISABLED: Reddit fetching generates too much off-topic/garbage content
        # Nexus focuses on Canadian news from RSS feeds only
        return []

    def _extract_image_url(self, post: Dict) -> str:
        """Extract image URL from Reddit post"""
        image_url = None
        thumbnail = post.get("thumbnail", "")

        if thumbnail and thumbnail.startswith("http"):
            image_url = thumbnail

        if "preview" in post and "images" in post["preview"]:
            try:
                image_url = post["preview"]["images"][0]["source"]["url"].replace(
                    "&amp;", "&"
                )
            except (KeyError, IndexError, TypeError):
                pass

        return image_url
