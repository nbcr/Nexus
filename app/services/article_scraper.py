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
    
    async def fetch_search_context(self, url: str) -> Optional[Dict]:
        """
        Fetch and parse search results from DuckDuckGo to provide context.
        Extracts instant answer boxes and top search results.
        Uses DuckDuckGo's Instant Answer API for rich content.
        
        Args:
            url: The DuckDuckGo search URL
            
        Returns:
            Dict with search results and context if successful
            None if scraping fails
        """
        try:
            print(f"🔍 Fetching search context from: {url}")
            
            # Extract search query from URL
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            query = params.get('q', ['unknown'])[0]
            
            # Use DuckDuckGo's Instant Answer API
            # This is a free, public API that doesn't require authentication
            api_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
            
            print(f"📡 Querying DuckDuckGo API: {api_url}")
            api_response = requests.get(api_url, headers=self.headers, timeout=self.timeout)
            api_response.raise_for_status()
            api_data = api_response.json()
            
            # Extract instant answer content
            instant_answer = None
            image_url = None
            
            # Abstract is the main description (like Wikipedia excerpt)
            abstract = api_data.get('Abstract', '').strip()
            if abstract:
                instant_answer = abstract
                image_url = api_data.get('Image', '')
            
            # If no abstract, try Definition
            if not instant_answer:
                definition = api_data.get('Definition', '').strip()
                if definition:
                    instant_answer = definition
            
            # Build context
            context_parts = []
            
            if instant_answer:
                context_parts.append(f"**{query}**\n")
                context_parts.append(instant_answer)
                
                # Add source if available
                source = api_data.get('AbstractSource', '')
                if source:
                    context_parts.append(f"\n\n*Source: {source}*")
                
                context_parts.append("\n" + "="*50)
            
            # Add related topics if available
            related_topics = api_data.get('RelatedTopics', [])
            if related_topics:
                context_parts.append(f"\n\n**Related Information:**\n")
                for i, topic in enumerate(related_topics[:5], 1):
                    if isinstance(topic, dict):
                        text = topic.get('Text', '')
                        if text:
                            context_parts.append(f"{i}. {text}")
            
            content = '\n'.join(context_parts) if context_parts else "No information found."
            
            search_data = {
                'url': url,
                'title': query,
                'content': content,
                'author': 'DuckDuckGo',
                'published_date': '',
                'image_url': image_url if image_url and len(image_url) > 10 else None,
                'domain': 'duckduckgo.com',
                'search_results': [],
                'instant_answer': instant_answer
            }
            
            print(f"✅ Extracted instant answer: {bool(instant_answer)}, Image: {bool(image_url)}")
            return search_data
                
        except Exception as e:
            print(f"❌ Error scraping search results: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_search_query(self, soup: BeautifulSoup, url: str) -> str:
        """Extract search query from page or URL"""
        # Try to get from URL parameter
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'q' in params:
            return params['q'][0]
        
        # Fallback: try to find on page
        query_input = soup.find('input', {'name': 'q'})
        if query_input and query_input.get('value'):
            return query_input.get('value')
        
        return "unknown query"
    
    def _extract_instant_answer(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract instant answer/infobox from search results.
        This includes Wikipedia snippets, knowledge panels, etc.
        """
        # Try multiple selectors for different instant answer formats
        
        # DuckDuckGo instant answer box
        instant_box = soup.find('div', class_=re.compile('module__text|zci-wrapper|ia-module'))
        if instant_box:
            text = instant_box.get_text(separator=' ', strip=True)
            if text and len(text) > 50:
                return text
        
        # Wikipedia/knowledge panel content
        kb_panel = soup.find('div', attrs={'data-area': 'infobox'})
        if not kb_panel:
            kb_panel = soup.find('div', class_=re.compile('infobox|knowledge-panel'))
        
        if kb_panel:
            # Get the main text description
            description = kb_panel.find('div', class_=re.compile('description|text|content'))
            if description:
                text = description.get_text(separator=' ', strip=True)
                if text and len(text) > 50:
                    return text
        
        # Try to find any prominent description or snippet at top of results
        # This often contains the answer
        top_content = soup.find('div', class_=re.compile('result--zero-click|abstract|answer'))
        if top_content:
            text = top_content.get_text(separator=' ', strip=True)
            if text and len(text) > 50:
                return text
        
        # Look for any highlighted/featured content
        featured = soup.find(['div', 'section'], class_=re.compile('featured|highlight|instant'))
        if featured:
            text = featured.get_text(separator=' ', strip=True)
            if text and len(text) > 50:
                return text
        
        return None
    
    def _extract_search_results(self, soup: BeautifulSoup) -> list:
        """Extract search results from DuckDuckGo page"""
        results = []
        
        # DuckDuckGo result selectors (may need adjustment)
        result_divs = soup.find_all('article', {'data-testid': re.compile('result')})
        if not result_divs:
            result_divs = soup.find_all('div', class_=re.compile('result'))
        
        for result_div in result_divs[:10]:  # Get top 10
            try:
                # Extract title
                title_elem = result_div.find('h2') or result_div.find('a', class_=re.compile('result__a'))
                title = title_elem.get_text().strip() if title_elem else ''
                
                # Extract snippet/description
                snippet_elem = result_div.find('div', class_=re.compile('snippet|result__snippet'))
                if not snippet_elem:
                    # Try finding any div with text
                    snippet_elem = result_div.find('span', class_=re.compile('result__snippet'))
                snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                
                # Extract URL
                link_elem = result_div.find('a', href=True)
                link = link_elem['href'] if link_elem else ''
                
                if title:  # Only add if we have at least a title
                    results.append({
                        'title': title,
                        'snippet': snippet,
                        'url': link
                    })
            except Exception as e:
                print(f"⚠️ Error parsing individual result: {e}")
                continue
        
        return results
    
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
