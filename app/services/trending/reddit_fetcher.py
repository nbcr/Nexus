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
        if not self.enabled:
            return []

        trends = []

        try:
            for subreddit_name, category in self.subreddits:
                try:
                    print(f"Fetching hot posts from r/{subreddit_name}")

                    url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit=10"
                    headers = {"User-Agent": "Nexus/1.0"}
                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code != 200:
                        print(
                            f"⚠️ Got status {response.status_code} for r/{subreddit_name}"
                        )
                        continue

                    data = response.json()
                    posts = data.get("data", {}).get("children", [])

                    post_count = 0
                    for post_data in posts:
                        post = post_data.get("data", {})

                        if post.get("stickied", False):
                            continue

                        score = post.get("score", 0)
                        num_comments = post.get("num_comments", 0)
                        trend_score = min(
                            0.95, 0.5 + (score / 10000) + (num_comments / 1000)
                        )

                        image_url = self._extract_image_url(post)

                        description = (
                            post.get("selftext", "")[:500]
                            if post.get("selftext")
                            else f"Posted in r/{subreddit_name}"
                        )

                        trend_data = {
                            "title": post.get("title", "Untitled"),
                            "original_query": post.get("title", "Untitled"),
                            "description": description,
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "source": f"r/{subreddit_name}",
                            "image_url": image_url,
                            "published": datetime.fromtimestamp(
                                post.get("created_utc", 0)
                            ).isoformat(),
                            "trend_score": trend_score,
                            "category": category,
                            "tags": ["reddit", subreddit_name, category.lower()],
                            "news_items": [
                                {
                                    "title": post.get("title", "Untitled"),
                                    "snippet": description,
                                    "url": f"https://reddit.com{post.get('permalink', '')}",
                                    "picture": image_url,
                                    "source": f"r/{subreddit_name}",
                                }
                            ],
                        }
                        trends.append(trend_data)
                        post_count += 1

                    print(f"✅ Added {post_count} posts from r/{subreddit_name}")
                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"⚠️ Error fetching r/{subreddit_name}: {e}")
                    continue

            print(f"✅ Successfully fetched {len(trends)} trends from Reddit")
            return trends

        except Exception as e:
            print(f"❌ Error in _fetch_reddit_trends: {e}")
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
