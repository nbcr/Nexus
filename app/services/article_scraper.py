"""
Article Scraper Service

Fetches and extracts readable article content from web pages.
Uses BeautifulSoup to parse HTML and extract main content.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import re
from urllib.parse import urlparse


class ArticleScraperService:
    """Service for scraping article content from web pages"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
    
    async def fetch_article(self, url: str) -> Optional[Dict]:
        """
        Fetch and parse article content from a URL.
        
        Args:
            url: The article URL to scrape
            
        Returns:
            Dict with title, content, author, date, and image_url if successful
            None if scraping fails
        """
        try:
            print(f"📰 Fetching article from: {url}")
            
            # Fetch the page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            article_data = {
                'url': url,
                'title': self._extract_title(soup),
                'content': self._extract_content(soup),
                'author': self._extract_author(soup),
                'published_date': self._extract_date(soup),
                'image_url': self._extract_image(soup, url),
                'domain': urlparse(url).netloc
            }
            
            # Validate we got meaningful content
            if article_data['content'] and len(article_data['content']) > 200:
                print(f"✅ Successfully scraped {len(article_data['content'])} characters")
                return article_data
            else:
                print(f"⚠️ Content too short or empty. Length: {len(article_data['content']) if article_data['content'] else 0}")
                print(f"Title: {article_data['title'][:100] if article_data['title'] else 'None'}")
                # Return article data anyway with what we have
                if article_data['title']:
                    print("ℹ️ Returning article with limited content")
                    # Set a message indicating content couldn't be extracted
                    article_data['content'] = f"Unable to extract full article content. Please visit the source site to read the full article."
                    return article_data
                return None
                
        except Exception as e:
            print(f"❌ Error scraping article: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
            'h1',
            ('h1', {'class': re.compile('title|headline', re.I)}),
            'title'
        ]
        
        for selector in selectors:
            if isinstance(selector, tuple):
                tag, attrs = selector
                element = soup.find(tag, attrs)
                if element:
                    return element.get('content', element.get_text().strip())
            else:
                element = soup.find(selector)
                if element:
                    return element.get_text().strip()
        
        return "Article"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Remove script, style, nav, footer, etc.
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()
        
        # Try to find article content container
        content_selectors = [
            ('article', {}),
            ('div', {'class': re.compile('article|content|post|entry', re.I)}),
            ('div', {'id': re.compile('article|content|post|entry', re.I)}),
            ('main', {}),
        ]
        
        article_element = None
        for tag, attrs in content_selectors:
            article_element = soup.find(tag, attrs)
            if article_element:
                break
        
        if not article_element:
            # Fallback: use body
            article_element = soup.find('body')
        
        if not article_element:
            return ""
        
        # Extract paragraphs
        paragraphs = []
        for p in article_element.find_all('p'):
            text = p.get_text().strip()
            # Filter out very short paragraphs (likely navigation/footer text)
            if len(text) > 50:
                paragraphs.append(text)
        
        content = '\n\n'.join(paragraphs)
        
        # Limit content length (optional)
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        return content
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        # Try multiple selectors
        selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('span', {'class': re.compile('author', re.I)}),
            ('a', {'class': re.compile('author', re.I)}),
            ('div', {'class': re.compile('author', re.I)}),
        ]
        
        for selector in selectors:
            if isinstance(selector, tuple):
                tag, attrs = selector
                element = soup.find(tag, attrs)
                if element:
                    return element.get('content', element.get_text().strip())
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date"""
        selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publish-date'}),
            ('time', {}),
            ('span', {'class': re.compile('date|time', re.I)}),
        ]
        
        for selector in selectors:
            if isinstance(selector, tuple):
                tag, attrs = selector
                element = soup.find(tag, attrs)
                if element:
                    return element.get('content') or element.get('datetime') or element.get_text().strip()
        
        return None
    
    def _extract_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract main article image"""
        selectors = [
            ('meta', {'property': 'og:image'}),
            ('meta', {'name': 'twitter:image'}),
        ]
        
        for selector in selectors:
            tag, attrs = selector
            element = soup.find(tag, attrs)
            if element:
                img_url = element.get('content')
                if img_url:
                    # Make absolute URL if relative
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        parsed = urlparse(base_url)
                        img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                    return img_url
        
        return None


# Global instance
article_scraper = ArticleScraperService()
