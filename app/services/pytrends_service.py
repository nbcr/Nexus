"""
PyTrends Service for fetching Google Trends data

Uses the pytrends library to fetch:
- Real-time trending searches
- Related topics and queries
- Interest over time
- Regional interest
"""

from pytrends.request import TrendReq
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
from functools import wraps
import pandas as pd
import requests


def async_wrap(func):
    """Wrapper to run synchronous pytrends calls in executor"""

    @wraps(func)
    async def run(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    return run


class PyTrendsService:
    def __init__(self):
        """Initialize PyTrends with Canada (CA) as default region"""
        self.pytrends = TrendReq(hl="en-CA", tz=360, timeout=(10, 25))
        self.geo = "CA"
        print("✅ PyTrends service initialized for Canada")

    async def fetch_trending_searches(self) -> List[Dict]:
        """
        Fetch today's trending searches from Google Trends.
        Returns a list of trending topics with metadata.

        Note: Google Trends API can be unreliable and may return 404 errors.
        This is expected behavior when Google limits access.
        """
        try:
            print("Fetching trending searches from Google Trends...")

            # Fetch trending searches for Canada
            @async_wrap
            def get_trending():
                return self.pytrends.trending_searches(pn=self.geo.lower())

            df = await get_trending()

            if df is None or df.empty:
                print("⚠️ No trending searches returned from Google Trends")
                return []

            trends = []
            for idx, search_term in df[0].items():
                trend_data = {
                    "title": search_term,
                    "original_query": search_term,
                    "description": f"Trending search in Canada: {search_term}",
                    "url": f"https://trends.google.com/trends/explore?geo={self.geo}&q={search_term}",
                    "source": "Google Trends",
                    "image_url": None,
                    "published": datetime.now().isoformat(),
                    "trend_score": max(
                        0.7, 1.0 - (idx * 0.02)
                    ),  # Higher score for top trends
                    "category": "Trending Search",
                    "tags": ["pytrends", "trending", "canada", "google"],
                    "news_items": [],
                }
                trends.append(trend_data)

            print(f"✅ Fetched {len(trends)} trending searches")
            return trends

        except Exception as e:
            print(f"⚠️ Google Trends API unavailable: {e}")
            print("   This is normal - Google often limits API access.")
            print("   Feed will use RSS and Reddit sources instead.")
            return []

    async def fetch_related_topics(
        self, keyword: str, timeframe: str = "now 7-d"
    ) -> List[Dict]:
        """
        Fetch related topics for a given keyword.

        Args:
            keyword: The search term to find related topics for
            timeframe: Time range (e.g., 'now 7-d', 'today 1-m', 'today 3-m')

        Returns:
            List of related topics with relevance scores
        """
        try:
            print(f"Fetching related topics for '{keyword}'...")

            @async_wrap
            def get_related():
                self.pytrends.build_payload(
                    [keyword], cat=0, timeframe=timeframe, geo=self.geo
                )
                return self.pytrends.related_topics()

            related = await get_related()

            if not related or keyword not in related:
                print(f"⚠️ No related topics data for '{keyword}'")
                return []

            topics = []
            if "rising" in related[keyword]:
                rising_df = related[keyword]["rising"]
                if rising_df is not None and not rising_df.empty:
                    for idx, row in rising_df.iterrows():
                        topic_title = row.get(
                            "topic_title", row.get("formattedValue", "Unknown")
                        )
                        topic_type = row.get("topic_type", "Unknown")
                        value = row.get("value", 0)

                        topic_data = {
                            "title": topic_title,
                            "original_query": topic_title,
                            "description": f"Rising topic related to {keyword} ({topic_type})",
                            "url": f"https://trends.google.com/trends/explore?geo={self.geo}&q={topic_title}",
                            "source": "Google Trends - Related",
                            "image_url": None,
                            "published": datetime.now().isoformat(),
                            "trend_score": min(0.95, 0.5 + (value / 200)),
                            "category": topic_type,
                            "tags": [
                                "pytrends",
                                "related",
                                keyword.lower(),
                                topic_type.lower(),
                            ],
                            "news_items": [],
                            "parent_keyword": keyword,
                        }
                        topics.append(topic_data)

            print(f"✅ Found {len(topics)} related topics for '{keyword}'")
            return topics

        except Exception as e:
            print(f"⚠️ Could not fetch related topics for '{keyword}': {e}")
            return []

    async def fetch_related_queries(
        self, keyword: str, timeframe: str = "now 7-d"
    ) -> List[Dict]:
        """
        Fetch related search queries for a given keyword and enrich with Google search context.

        Args:
            keyword: The search term to find related queries for
            timeframe: Time range (e.g., 'now 7-d', 'today 1-m', 'today 3-m')

        Returns:
            List of related queries with relevance scores and contextual descriptions
        """
        try:
            print(f"Fetching related queries for '{keyword}'...")

            @async_wrap
            def get_queries():
                self.pytrends.build_payload(
                    [keyword], cat=0, timeframe=timeframe, geo=self.geo
                )
                return self.pytrends.related_queries()

            related = await get_queries()

            queries = []
            if keyword in related and "rising" in related[keyword]:
                rising_df = related[keyword]["rising"]
                if rising_df is not None and not rising_df.empty:
                    for idx, row in rising_df.iterrows():
                        query = row.get("query", "Unknown")
                        value = row.get("value", 0)

                        # Fetch context from DuckDuckGo
                        context = await self._fetch_duckduckgo_context(query)

                        query_data = {
                            "title": query,
                            "original_query": query,
                            "description": context.get(
                                "description",
                                self._create_query_description(query, keyword),
                            ),
                            "url": context.get(
                                "url",
                                f"https://www.google.com/search?q={query.replace(' ', '+')}",
                            ),
                            "source": context.get("source", "Search"),
                            "image_url": context.get("image_url"),
                            "published": datetime.now().isoformat(),
                            "trend_score": min(0.95, 0.5 + (value / 200)),
                            "category": context.get(
                                "category", self._infer_category_from_query(query)
                            ),
                            "tags": ["pytrends", "query", keyword.lower()],
                            "news_items": [],
                            "parent_keyword": keyword,
                        }
                        queries.append(query_data)

                        # Small delay to be respectful
                        await asyncio.sleep(0.3)

            print(
                f"✅ Found {len(queries)} related queries with context for '{keyword}'"
            )
            return queries

        except Exception as e:
            print(f"❌ Error fetching related queries for '{keyword}': {e}")
            return []

    async def fetch_interest_over_time(
        self, keywords: List[str], timeframe: str = "now 7-d"
    ) -> Dict:
        """
        Fetch interest over time data for keywords.

        Args:
            keywords: List of search terms (max 5)
            timeframe: Time range (e.g., 'now 7-d', 'today 1-m', 'today 3-m')

        Returns:
            Dictionary with interest data over time
        """
        try:
            if len(keywords) > 5:
                keywords = keywords[:5]
                print(f"⚠️ Limited to 5 keywords: {keywords}")

            print(f"Fetching interest over time for {keywords}...")

            @async_wrap
            def get_interest():
                self.pytrends.build_payload(
                    keywords, cat=0, timeframe=timeframe, geo=self.geo
                )
                return self.pytrends.interest_over_time()

            df = await get_interest()

            if df is not None and not df.empty:
                # Convert to dict for easier processing
                interest_data = {
                    "keywords": keywords,
                    "timeframe": timeframe,
                    "data": df.to_dict("records"),
                    "peak_dates": {},
                }

                # Find peak interest dates for each keyword
                for keyword in keywords:
                    if keyword in df.columns:
                        peak_idx = df[keyword].idxmax()
                        interest_data["peak_dates"][keyword] = str(peak_idx)

                print(f"✅ Fetched interest data for {len(keywords)} keywords")
                return interest_data

            return {"keywords": keywords, "data": [], "peak_dates": {}}

        except Exception as e:
            print(f"❌ Error fetching interest over time: {e}")
            return {"keywords": keywords, "data": [], "peak_dates": {}}

    def _create_query_description(self, query: str, parent_keyword: str) -> str:
        """Create a meaningful description for a trending query without web scraping"""
        query_lower = query.lower()

        # Identify query types and create contextual descriptions
        if any(word in query_lower for word in ["vs", "versus"]):
            return f"People are comparing: {query}"
        elif query_lower.endswith(" meaning"):
            word = query_lower.replace(" meaning", "")
            return f"Many people are looking up the meaning of '{word}'"
        elif any(
            word in query_lower
            for word in ["who is", "what is", "where is", "when is", "why is", "how"]
        ):
            return f"Trending question: {query}"
        elif any(word in query_lower for word in ["record", "stats", "statistics"]):
            return f"People are checking stats for: {query}"
        elif any(word in query_lower for word in ["next", "upcoming", "schedule"]):
            return f"Trending search for upcoming events: {query}"
        elif any(word in query_lower for word in ["fight", "match", "game", "race"]):
            return f"Sports/competition trending: {query}"
        elif any(word in query_lower for word in ["logo", "symbol", "image"]):
            return f"Visual search trending: {query}"
        elif any(
            word in query_lower
            for word in ["age", "height", "weight", "birthday", "born"]
        ):
            return f"People want to know more about: {query}"
        elif any(
            word in query_lower
            for word in ["cast", "trailer", "release date", "movie", "show"]
        ):
            return f"Entertainment search: {query}"
        elif len(query.split()) == 1:
            return f"Rising interest in: {query}"
        else:
            return f"Trending search related to {parent_keyword}: {query}"

    def _infer_category_from_query(self, query: str) -> str:
        """Infer category from the query itself"""
        query_lower = query.lower()

        if any(
            word in query_lower
            for word in ["ufc", "fight", "fighter", "boxing", "mma", "wrestling"]
        ):
            return "Combat Sports"
        elif any(
            word in query_lower
            for word in [
                "nfl",
                "nhl",
                "nba",
                "mlb",
                "soccer",
                "football",
                "hockey",
                "basketball",
            ]
        ):
            return "Sports"
        elif any(
            word in query_lower for word in ["meaning", "definition", "translate"]
        ):
            return "Reference"
        elif any(
            word in query_lower
            for word in ["movie", "show", "actor", "netflix", "series", "trailer"]
        ):
            return "Entertainment"
        elif any(
            word in query_lower
            for word in ["tech", "app", "software", "iphone", "android", "computer"]
        ):
            return "Technology"
        elif any(
            word in query_lower
            for word in ["ceo", "company", "stock", "business", "market"]
        ):
            return "Business"
        elif any(
            word in query_lower for word in ["news", "breaking", "update", "latest"]
        ):
            return "News"
        else:
            return "Trending"

    async def _fetch_duckduckgo_context(self, query: str) -> Dict:
        """
        Fetch contextual information from DuckDuckGo Instant Answer API.
        DuckDuckGo is more scraping-friendly than Google.
        """
        try:
            print(f"🦆 Fetching DuckDuckGo context for '{query}'...")

            # Try DuckDuckGo Instant Answer API first (free, no auth needed)
            api_url = f"https://api.duckduckgo.com/?q={query.replace(' ', '+')}&format=json&no_html=1&skip_disambig=1"

            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Extract the best available description
                description = None
                source_url = None

                # Try Abstract (usually from Wikipedia)
                if data.get("Abstract"):
                    description = data["Abstract"][:300]
                    source_url = data.get("AbstractURL")
                    print(f"✅ Found Abstract: {description[:50]}...")

                # Try Definition
                elif data.get("Definition"):
                    description = data["Definition"][:300]
                    source_url = data.get("DefinitionURL")
                    print(f"✅ Found Definition: {description[:50]}...")

                # Try Answer (direct answer)
                elif data.get("Answer"):
                    description = data["Answer"][:300]
                    print(f"✅ Found Answer: {description[:50]}...")

                # Try Related Topics
                elif data.get("RelatedTopics") and len(data["RelatedTopics"]) > 0:
                    first_topic = data["RelatedTopics"][0]
                    if isinstance(first_topic, dict) and first_topic.get("Text"):
                        description = first_topic["Text"][:300]
                        source_url = first_topic.get("FirstURL")
                        print(f"✅ Found Related Topic: {description[:50]}...")

                # Extract image if available
                image_url = data.get("Image") if data.get("Image") else None

                if description:
                    return {
                        "description": description,
                        "url": source_url
                        or f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                        "source": data.get("AbstractSource", "DuckDuckGo"),
                        "image_url": image_url,
                        "category": self._infer_category_from_query(query),
                    }
                else:
                    print(f"⚠️ DuckDuckGo returned no content for '{query}'")
            else:
                print(f"⚠️ DuckDuckGo API returned {response.status_code}")

            # Fallback to local description generation
            return {
                "description": self._create_query_description(query, ""),
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "source": "Search",
                "image_url": None,
                "category": self._infer_category_from_query(query),
            }

        except Exception as e:
            print(f"⚠️ Error fetching DuckDuckGo context for '{query}': {e}")
            return {
                "description": self._create_query_description(query, ""),
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "source": "Search",
                "image_url": None,
                "category": self._infer_category_from_query(query),
            }

    async def enrich_trends_with_pytrends(
        self, base_trends: List[Dict], max_topics: int = 5
    ) -> List[Dict]:
        """
        Enrich existing trends with related topics and queries from pytrends.

        Args:
            base_trends: List of existing trend data
            max_topics: Maximum number of base trends to enrich (to avoid rate limits)

        Returns:
            Combined list of original trends plus related content
        """
        all_trends = list(base_trends)  # Start with base trends
        related_count = 0

        try:
            # Take top trends and find related content
            top_trends = base_trends[:max_topics]

            for idx, trend in enumerate(top_trends, 1):
                keyword = trend.get("original_query", trend.get("title", ""))
                if not keyword:
                    continue

                print(
                    f"🔍 [{idx}/{len(top_trends)}] Enriching '{keyword}' with PyTrends..."
                )

                # Fetch related topics and queries
                related_topics = await self.fetch_related_topics(
                    keyword, timeframe="now 1-d"
                )
                related_queries = await self.fetch_related_queries(
                    keyword, timeframe="now 1-d"
                )

                # Add top items to overall trends
                added_topics = related_topics[:2]  # Top 2 related topics
                added_queries = related_queries[:2]  # Top 2 related queries

                all_trends.extend(added_topics)
                all_trends.extend(added_queries)

                related_count += len(added_topics) + len(added_queries)

                if added_topics or added_queries:
                    print(
                        f"   ✅ Added {len(added_topics)} topics + {len(added_queries)} queries for '{keyword}'"
                    )

                # Delay between keywords to avoid rate limiting
                if idx < len(top_trends):
                    await asyncio.sleep(2)

            print(
                f"🎨 Enrichment complete: {len(base_trends)} base + {related_count} related = {len(all_trends)} total"
            )
            return all_trends

        except Exception as e:
            print(f"⚠️ Error enriching trends: {e}")
            return base_trends  # Return original trends if enrichment fails


# Global instance
pytrends_service = PyTrendsService()
