import feedparser # type: ignore
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # type: ignore

from app.models import Topic, ContentItem
from app.core.config import settings


class TrendingService:
    def __init__(self):
        self.feed_url = "https://trends.google.com/trending/rss?geo=CA"
    
    async def fetch_canada_trends(self) -> List[Dict]:
        """Fetch trending topics from Google Trends Canada RSS feed"""
        try:
            print(f"Fetching from Google Trends: {self.feed_url}")
            feed = feedparser.parse(self.feed_url)
            
            trends = []
            for entry in feed.entries[:15]:
                print(f"Processing entry: {entry}")  # Debug log
                
                # Extract data from the Google Trends specific fields
                title = getattr(entry, 'title', '').strip()
                description = (getattr(entry, 'ht_news_item_snippet', '') or 
                             getattr(entry, 'summary', '') or 
                             getattr(entry, 'description', ''))
                url = getattr(entry, 'ht_news_item_url', '') or getattr(entry, 'link', '')
                
                # Extract news items
                news_items = []
                try:
                    # Debug print the entry structure
                    print(f"Entry has ht_news_item? {hasattr(entry, 'ht_news_item')}")
                    if hasattr(entry, 'ht_news_item'):
                        print(f"News item type: {type(entry.ht_news_item)}")
                        print(f"News item content: {entry.ht_news_item}")
                    
                    # Look for individual news item fields
                    news_item = {
                        'title': getattr(entry, 'ht_news_item_title', '').strip(),
                        'snippet': getattr(entry, 'ht_news_item_snippet', '').strip(),
                        'url': getattr(entry, 'ht_news_item_url', ''),
                        'picture': getattr(entry, 'ht_news_item_picture', ''),
                        'source': getattr(entry, 'ht_news_item_source', 'News').strip()
                    }
                    
                    # If we have a direct news item with title and URL, add it
                    if news_item['title'] and news_item['url']:
                        news_items.append(news_item)
                    
                    # Check for nested news items structure
                    if hasattr(entry, 'ht_news_item'):
                        items = []
                        if isinstance(entry.ht_news_item, list):
                            items = entry.ht_news_item
                        elif isinstance(entry.ht_news_item, dict):
                            items = [entry.ht_news_item]
                        elif hasattr(entry.ht_news_item, 'ht_news_item_title'):
                            # Single news item object
                            items = [entry.ht_news_item]
                            
                        for item in items:
                            news_item = {
                                'title': getattr(item, 'ht_news_item_title', '').strip(),
                                'snippet': getattr(item, 'ht_news_item_snippet', '').strip(),
                                'url': getattr(item, 'ht_news_item_url', ''),
                                'picture': getattr(item, 'ht_news_item_picture', ''),
                                'source': getattr(item, 'ht_news_item_source', 'News').strip()
                            }
                            if news_item['title'] and news_item['url']:
                                news_items.append(news_item)
                except Exception as e:
                    print(f"Error processing news items for entry {entry.get('title', 'Unknown')}: {str(e)}")
                
                # Set the main image and source from the first news item if available
                image_url = None
                source = 'News'
                
                if news_items:
                    first_news = news_items[0]
                    image_url = first_news['picture']
                    source = first_news['source']
                else:
                    # Fallback to entry-level ht: attributes if no news items
                    image_url = getattr(entry, 'ht_picture', None)
                    source = getattr(entry, 'ht_picture_source', 'News')
                
                # Generate a summary title based on news items
                summary_title = self._generate_summary_title(title, news_items)

                trend_data = {
                    'title': summary_title,  # Use the generated summary title
                    'original_query': title,  # Keep the original search term
                    'description': description,
                    'url': url,
                    'source': source,
                    'image_url': image_url,
                    'published': entry.get('published', ''),
                    'trend_score': self._calculate_trend_score(entry),
                    'category': self._extract_category(entry),
                    'tags': self._extract_tags(entry),
                    'news_items': news_items
                }
                trends.append(trend_data)
            
            print(f"✅ Successfully fetched {len(trends)} trends from Google Trends")
            return trends
            
        except Exception as e:
            print(f"❌ Error fetching Google Trends: {e}")
            return []
    
    def _extract_news_item(self, entry) -> Dict:
        """Extract news item data from Google Trends entry"""
        news_item = {
            'source': 'News',
            'picture': None
        }
        
        # Look for ht:news_item fields in the entry
        if hasattr(entry, 'ht_news_item_source'):
            news_item['source'] = entry.ht_news_item_source
        elif hasattr(entry, 'news_item_source'):
            news_item['source'] = entry.news_item_source
        
        if hasattr(entry, 'ht_news_item_picture'):
            news_item['picture'] = entry.ht_news_item_picture
        elif hasattr(entry, 'news_item_picture'):
            news_item['picture'] = entry.news_item_picture
            
        return news_item
    
    def _calculate_trend_score(self, entry) -> float:
        """Calculate trend score based on position in feed"""
        return 0.7
    
    def _extract_category(self, entry) -> str:
        """Extract category from entry"""
        categories = entry.get('tags', [])
        if categories and hasattr(categories[0], 'term'):
            return categories[0].term
        return "General"
    
    def _extract_tags(self, entry) -> List[str]:
        """Extract tags from entry"""
        tags = ['trending', 'canada', 'google trends']
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if hasattr(tag, 'term'):
                    tags.append(tag.term.lower())
        return list(set(tags))

    def _generate_summary_title(self, original_title: str, news_items: List[Dict]) -> str:
        """Generate a summary title based on news items and original trend title"""
        try:
            if not news_items:
                return original_title.title()  # Just capitalize the original title if no news items

            # Get the most recent news item (assuming it's most relevant)
            main_news = news_items[0]
            
            # Extract key information
            title = main_news.get('title', '').strip()
            snippet = main_news.get('snippet', '').strip()
            source = main_news.get('source', '').strip()

            # If we have a good news title, use it as base
            if title:
                # Clean up the title
                # Remove source names from title if they appear at the start or end
                for s in [source, 'Report:', 'BREAKING:', 'UPDATE:', '- CNN', '- BBC', '| CBC News']:
                    title = title.replace(s, '').strip()
                
                # If the original trend query appears in the title, ensure it's properly highlighted
                if original_title.lower() in title.lower():
                    return title.strip()
                
                # Otherwise, create a context-aware title
                return f"{original_title.title()}: {title}"
            
            # Fallback to original title if we couldn't generate a better one
            return original_title.title()

        except Exception as e:
            print(f"Error generating summary title: {e}")
            return original_title.title()
    
    async def generate_ai_summary(self, trend_title: str, trend_description: str = "") -> str:
        """Generate AI summary for trending topics"""
        if trend_description:
            return trend_description
        return f"Trending topic in Canada: {trend_title}"
    
    async def save_trends_to_database(self, db: AsyncSession) -> List[Topic]:
        """Fetch trends and save them to database"""
        trends = await self.fetch_canada_trends()
        saved_topics = []
        
        for trend_data in trends:
            try:
                normalized_title = trend_data['title'].lower().replace(' ', '_')[:190]
                
                # Check if topic already exists
                result = await db.execute(
                    select(Topic).where(Topic.normalized_title == normalized_title)
                )
                existing_topic = result.scalar_one_or_none()
                
                if not existing_topic:
                    topic = Topic(
                        title=trend_data['title'],
                        normalized_title=normalized_title,
                        description=trend_data.get('description', ''),
                        category=trend_data.get('category', 'Trending'),
                        trend_score=trend_data.get('trend_score', 0.7),
                        tags=trend_data.get('tags', ['trending', 'canada', 'google trends'])
                    )
                    db.add(topic)
                    await db.flush()
                    
                    ai_summary = await self.generate_ai_summary(
                        trend_data['title'], 
                        trend_data.get('description', '')
                    )
                    
                    content_item = ContentItem(
                        topic_id=topic.id,
                        content_type="trending_analysis",
                        content_text=ai_summary,
                        ai_model_used="google_trends_analyzer_v1",
                        source_urls=[trend_data.get('url', '')],
                        is_published=True
                    )
                    db.add(content_item)
                    
                    saved_topics.append(topic)
                    print(f"✅ Saved trend: {trend_data['title']} (Source: {trend_data['source']})")
                    
            except Exception as e:
                print(f"❌ Error saving trend '{trend_data['title']}': {e}")
                continue
        
        await db.commit()
        
        for topic in saved_topics:
            await db.refresh(topic)
        
        print(f"🎯 Total trends saved to database: {len(saved_topics)}")
        return saved_topics


# Global instance
trending_service = TrendingService()
