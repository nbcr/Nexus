"""
Async RSS Feed Parser

Replaces blocking feedparser with fully async implementation using aiohttp + xmltodict.
Optimized for concurrent I/O-bound RSS feed fetching with connection pooling.
"""

import aiohttp
import xmltodict
from typing import List, Dict, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime
import asyncio

# Constants
TEXT_KEY = "#text"


class AsyncRSSParser:
    """Async RSS/Atom feed parser with connection pooling"""

    def __init__(self, max_connections: int = 100, timeout: int = 10):
        """
        Initialize parser with connection pooling.

        Args:
            max_connections: Maximum concurrent connections
            timeout: Request timeout in seconds
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.connector = aiohttp.TCPConnector(limit=max_connections, ttl_dns_cache=300)
        self._session: Optional[aiohttp.ClientSession] = None

    def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=self.connector, timeout=self.timeout
            )
        return self._session

    async def close(self):
        """Close the aiohttp session and connector"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def parse_feed(self, feed_url: str) -> Dict:
        """
        Parse RSS/Atom feed from URL asynchronously.

        Args:
            feed_url: URL of the RSS/Atom feed

        Returns:
            Dict with 'feed' metadata and 'entries' list
        """
        try:
            session = self.get_session()
            async with session.get(feed_url) as response:
                if response.status != 200:
                    return {"feed": {}, "entries": []}

                content = await response.text()

            # Parse XML to dict
            parsed = xmltodict.parse(content)

            # Handle RSS 2.0
            if "rss" in parsed:
                return self._parse_rss(parsed["rss"])
            # Handle Atom
            elif "feed" in parsed:
                return self._parse_atom(parsed["feed"])
            else:
                return {"feed": {}, "entries": []}

        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
            return {"feed": {}, "entries": []}

    def _parse_rss(self, rss_data: Dict) -> Dict:
        """Parse RSS 2.0 format"""
        channel = rss_data.get("channel", {})
        entries = channel.get("item", [])

        # Ensure entries is a list
        if not isinstance(entries, list):
            entries = [entries] if entries else []

        return {
            "feed": {
                "title": channel.get("title", ""),
                "link": channel.get("link", ""),
                "description": channel.get("description", ""),
                "language": channel.get("language", ""),
                "updated": channel.get("lastBuildDate", ""),
            },
            "entries": [self._parse_rss_entry(entry) for entry in entries],
        }

    def _parse_atom(self, feed_data: Dict) -> Dict:
        """Parse Atom format"""
        entries = feed_data.get("entry", [])

        # Ensure entries is a list
        if not isinstance(entries, list):
            entries = [entries] if entries else []

        return {
            "feed": {
                "title": (
                    feed_data.get("title", {}).get("#text", "")
                    if isinstance(feed_data.get("title"), dict)
                    else feed_data.get("title", "")
                ),
                "link": self._extract_atom_link(feed_data.get("link", [])),
                "description": (
                    feed_data.get("subtitle", {}).get("#text", "")
                    if isinstance(feed_data.get("subtitle"), dict)
                    else feed_data.get("subtitle", "")
                ),
                "updated": feed_data.get("updated", ""),
            },
            "entries": [self._parse_atom_entry(entry) for entry in entries],
        }

    def _parse_rss_entry(self, entry: Dict) -> Dict:
        """Parse RSS entry/item"""
        return {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "description": entry.get("description", ""),
            "summary": entry.get("description", ""),
            "published": entry.get("pubDate", ""),
            "author": entry.get("author", "") or entry.get("dc:creator", ""),
            "tags": self._extract_rss_tags(entry),
            "media_content": entry.get("media:content"),
            "media_thumbnail": entry.get("media:thumbnail"),
            "enclosures": entry.get("enclosure"),
            "published_parsed": self._parse_date(entry.get("pubDate", "")),
        }

    def _parse_atom_entry(self, entry: Dict) -> Dict:
        """Parse Atom entry"""
        return {
            "title": (
                entry.get("title", {}).get("#text", "")
                if isinstance(entry.get("title"), dict)
                else entry.get("title", "")
            ),
            "link": self._extract_atom_link(entry.get("link", [])),
            "description": (
                entry.get("summary", {}).get(TEXT_KEY, "")
                if isinstance(entry.get("summary"), dict)
                else entry.get("summary", "")
            ),
            "summary": (
                entry.get("summary", {}).get(TEXT_KEY, "")
                if isinstance(entry.get("summary"), dict)
                else entry.get("summary", "")
            ),
            "published": entry.get("published", "") or entry.get("updated", ""),
            "author": self._extract_atom_author(entry.get("author")),
            "tags": self._extract_atom_tags(entry.get("category", [])),
            "published_parsed": self._parse_date(
                entry.get("published", "") or entry.get("updated", "")
            ),
        }

    def _extract_rss_tags(self, entry: Dict) -> List[str]:
        """Extract tags/categories from RSS entry"""
        tags = []
        category = entry.get("category", [])

        if isinstance(category, list):
            tags.extend(
                [c.get(TEXT_KEY, c) if isinstance(c, dict) else c for c in category]
            )
        elif category:
            tags.append(
                category.get(TEXT_KEY, category)
                if isinstance(category, dict)
                else category
            )

        return tags

    def _extract_atom_tags(self, categories) -> List[str]:
        """Extract tags from Atom entry"""
        if not categories:
            return []

        if not isinstance(categories, list):
            categories = [categories]

        tags = []
        for cat in categories:
            if isinstance(cat, dict):
                tags.append(cat.get("@term", ""))
            elif isinstance(cat, str):
                tags.append(cat)

        return [t for t in tags if t]

    def _extract_atom_link(self, links) -> str:
        """Extract URL from Atom link element"""
        if not links:
            return ""

        if not isinstance(links, list):
            links = [links]

        for link in links:
            if isinstance(link, dict):
                if link.get("@rel") == "alternate" or not link.get("@rel"):
                    return link.get("@href", "")
            elif isinstance(link, str):
                return link

        # Fallback: return first link
        if links and isinstance(links[0], dict):
            return links[0].get("@href", "")

        return ""

    def _extract_atom_author(self, author) -> str:
        """Extract author name from Atom author element"""
        if not author:
            return ""

        if isinstance(author, dict):
            return (
                author.get("name", {}).get(TEXT_KEY, "")
                if isinstance(author.get("name"), dict)
                else author.get("name", "")
            )
        elif isinstance(author, str):
            return author

        return ""

    def _parse_date(self, date_str: str) -> Optional[tuple]:
        """Parse date string to time tuple"""
        if not date_str:
            return None

        try:
            # Try RFC 2822 format (RSS)
            dt = parsedate_to_datetime(date_str)
            return dt.timetuple()[:9]
        except (ValueError, TypeError, AttributeError):
            pass

        try:
            # Try ISO 8601 format (Atom)
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.timetuple()[:9]
        except (ValueError, TypeError, AttributeError):
            pass

        return None


# Global instance with connection pooling
async_rss_parser = AsyncRSSParser(max_connections=50, timeout=10)
