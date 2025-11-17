#!/usr/bin/env python3
"""
Script to scrape content for existing PyTrends items.
Attempts to scrape DuckDuckGo search results for each PyTrends item.
Only hides items if scraping fails or returns no content.
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import ContentItem
from app.services.article_scraper import article_scraper

async def scrape_pytrends_items():
    """Scrape content for PyTrends items, hide only if scraping fails"""
    async with AsyncSessionLocal() as db:
        # Find all published PyTrends items without meaningful content
        result = await db.execute(
            select(ContentItem).where(
                ContentItem.content_type == 'trending_analysis',
                ContentItem.is_published == True
            )
        )
        
        items_to_process = []
        all_items = result.scalars().all()
        
        for item in all_items:
            # Check if item already has good content
            has_content = (
                item.content_text and 
                not item.content_text.startswith('Trending topic') and
                len(item.content_text) > 200
            )
            
            has_picture = (
                item.source_metadata and 
                item.source_metadata.get('picture_url') and 
                len(str(item.source_metadata.get('picture_url', ''))) > 10
            )
            
            # Only process if it lacks content or picture
            if not has_content or not has_picture:
                items_to_process.append(item)
        
        if not items_to_process:
            print("✅ All PyTrends items already have content!")
            return
        
        print(f"Found {len(items_to_process)} PyTrends items to scrape")
        print(f"This may take a while...\n")
        
        scraped_count = 0
        hidden_count = 0
        failed_count = 0
        
        for i, item in enumerate(items_to_process, 1):
            title = item.title or "Untitled"
            print(f"[{i}/{len(items_to_process)}] Processing: {title}")
            
            # Get the source URL (should be a search URL)
            if not item.source_urls or len(item.source_urls) == 0:
                print(f"  ❌ No source URL - hiding")
                item.is_published = False
                hidden_count += 1
                continue
            
            source_url = item.source_urls[0]
            
            try:
                # Try to scrape the article/search results
                article_data = await article_scraper.fetch_article(source_url)
                
                if article_data and article_data.get('content') and len(article_data['content']) > 200:
                    # Successfully scraped content
                    item.content_text = article_data['content']
                    
                    if article_data.get('title'):
                        item.title = article_data['title']
                    
                    if article_data.get('author'):
                        if not item.source_metadata:
                            item.source_metadata = {}
                        item.source_metadata['author'] = article_data['author']
                    
                    if article_data.get('published_date'):
                        if not item.source_metadata:
                            item.source_metadata = {}
                        item.source_metadata['published_date'] = article_data['published_date']
                    
                    print(f"  ✅ Scraped {len(article_data['content'])} chars of content")
                    scraped_count += 1
                else:
                    # Scraping returned no useful content - hide it
                    print(f"  ⚠️ No content returned - hiding")
                    item.is_published = False
                    hidden_count += 1
                    
            except Exception as e:
                error_msg = str(e).lower()
                if 'rate' in error_msg or 'limit' in error_msg or '429' in error_msg:
                    print(f"  ⏸️ Rate limited - stopping to avoid further limits")
                    print(f"\nStopped at item {i}/{len(items_to_process)}")
                    print(f"Run this script again later to continue scraping remaining items")
                    failed_count += 1
                    break
                else:
                    print(f"  ❌ Error: {e} - hiding")
                    item.is_published = False
                    hidden_count += 1
            
            # Small delay to avoid rate limiting
            if i < len(items_to_process):
                await asyncio.sleep(0.5)
        
        await db.commit()
        
        print(f"\n{'='*50}")
        print(f"✅ Scraped: {scraped_count} items")
        print(f"🙈 Hidden: {hidden_count} items (no content available)")
        print(f"❌ Failed: {failed_count} items (rate limited)")
        print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(scrape_pytrends_items())
