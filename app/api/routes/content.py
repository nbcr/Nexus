from fastapi import APIRouter, HTTPException, Depends, Query, Request, Cookie # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # pyright: ignore[reportMissingImports]
from typing import List, Optional
from datetime import datetime

from app.db import AsyncSessionLocal
from app.models import ContentItem, Topic
from app.schemas import ContentItem as ContentItemSchema, ContentWithTopic, Topic as TopicSchema
from app.services.content_recommendation import recommendation_service
from app.services.article_scraper import article_scraper
from app.services.deduplication import deduplication_service

from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

class CategoriesResponse(BaseModel):
    categories: List[str]

@router.get("/categories", response_model=CategoriesResponse)
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """Return all unique categories from ContentItem and Topic tables."""
    import logging
    logger = logging.getLogger("uvicorn.error")
    try:
        from sqlalchemy import select, distinct
        categories = set()
        result1 = await db.execute(select(distinct(ContentItem.category)).where(ContentItem.category.isnot(None)))
        categories.update([row[0] for row in result1.fetchall() if row[0]])
        result2 = await db.execute(select(distinct(Topic.category)).where(Topic.category.isnot(None)))
        categories.update([row[0] for row in result2.fetchall() if row[0]])
        return CategoriesResponse(categories=sorted(categories))
    except Exception as e:
        logger.error(f"Error in /categories endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Cookie # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # pyright: ignore[reportMissingImports]
from typing import List, Optional
from datetime import datetime

from app.db import AsyncSessionLocal
from app.models import ContentItem, Topic
from app.schemas import ContentItem as ContentItemSchema, ContentWithTopic, Topic as TopicSchema
from app.services.content_recommendation import recommendation_service
from app.services.article_scraper import article_scraper
from app.services.deduplication import deduplication_service

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@router.get("/feed")
async def get_personalized_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: Optional[str] = Query(None),
    exclude_ids: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    nexus_session: Optional[str] = Cookie(default=None)
):
    """
    Get personalized content feed with cursor-based pagination.
    Shows newest content first and prevents duplicates.
    """
    # Parse exclude_ids
    excluded_ids = []
    if exclude_ids:
        try:
            excluded_ids = [int(id.strip()) for id in exclude_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exclude_ids format")
    
    # Get session token for anonymous users
    session_token = nexus_session or request.cookies.get("nexus_session")
    
    # For now, we'll just use session-based recommendations
    # User authentication can be added later
    user_id = None
    
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info(f"Feed request: page={page}, category={category}, exclude_ids={exclude_ids}, cursor={cursor}")
    # Get personalized feed
    if category:
        logger.info(f"Filtering feed by category: {category}")
        result = await recommendation_service.get_trending_feed(
            db=db,
            page=page,
            page_size=page_size,
            category=category,
            exclude_ids=excluded_ids,
            cursor=cursor
        )
    else:
        result = await recommendation_service.get_personalized_feed(
            db=db,
            user_id=user_id,
            session_token=session_token,
            page=page,
            page_size=page_size,
            exclude_ids=excluded_ids,
            cursor=cursor
        )
    
    return {
        "page": page,
        "page_size": page_size,
        "items": result["items"],
        "next_cursor": result["next_cursor"],
        "has_more": result["has_more"],
        "is_personalized": session_token is not None
    }

@router.get("/trending-feed")
async def get_trending_feed_endpoint(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    category: Optional[str] = Query(None),
    exclude_ids: Optional[str] = Query(None)
):
    """
    Get trending content feed (non-personalized).
    """
    # Parse exclude_ids
    excluded_ids = []
    if exclude_ids:
        try:
            excluded_ids = [int(id.strip()) for id in exclude_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exclude_ids format")
    
    feed_items = await recommendation_service.get_trending_feed(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        exclude_ids=excluded_ids
    )
    
    return {
        "page": page,
        "page_size": page_size,
        "items": feed_items,
        "has_more": len(feed_items) == page_size
    }

@router.get("/", response_model=List[ContentWithTopic])
async def get_content_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all content items with their topics"""
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .where(ContentItem.title.isnot(None))  # Skip records with NULL titles
        .offset(skip)
        .limit(limit)
    )
    
    content_items = []
    for content_item, topic in result.all():
        content_dict = ContentItemSchema.model_validate(content_item).model_dump()
        content_dict["topic"] = TopicSchema.model_validate(topic).model_dump()
        content_items.append(content_dict)
    
    return content_items

@router.get("/{content_id}", response_model=ContentWithTopic)
async def get_content_item(content_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific content item with its topic"""
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .where(ContentItem.id == content_id)
    )
    
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    content_item, topic = row
    content_dict = ContentItemSchema.model_validate(content_item).model_dump()
    content_dict["topic"] = TopicSchema.model_validate(topic).model_dump()
    
    return content_dict

@router.get("/snippet/{content_id}")
async def get_content_snippet(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch and store article snippet/content on demand.
    Scrapes full article content and stores it in database.
    Returns snippet with rate limit handling.
    """
    # Get content item from database
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Check if we already have scraped content stored
    if content.content_text and len(content.content_text) > 100 and not content.content_text.startswith('Trending topic'):
        # Already scraped, return it
        snippet = content.content_text[:800] if len(content.content_text) > 800 else content.content_text
        return {"snippet": snippet, "full_content_available": True}
    
    # Get the source URL
    if not content.source_urls or len(content.source_urls) == 0:
        return {"snippet": content.description or None, "rate_limited": False}
    
    source_url = content.source_urls[0]
    
    # Scrape the article and store full content
    try:
        article_data = await article_scraper.fetch_article(source_url)
        if article_data and article_data.get('content'):
            # Store the full scraped content in database
            content.content_text = article_data['content']
            if article_data.get('title'):
                content.title = article_data['title']
            if article_data.get('author'):
                if not content.source_metadata:
                    content.source_metadata = {}
                content.source_metadata['author'] = article_data['author']
            if article_data.get('published_date'):
                if not content.source_metadata:
                    content.source_metadata = {}
                content.source_metadata['published_date'] = article_data['published_date']
            
            await db.commit()
            
            # Return snippet (first 800 chars)
            snippet = article_data['content'][:800] if len(article_data['content']) > 800 else article_data['content']
            return {"snippet": snippet, "full_content_available": True, "rate_limited": False}
    except Exception as e:
        error_msg = str(e).lower()
        # Check for rate limiting errors
        if 'rate' in error_msg or 'limit' in error_msg or '429' in error_msg or 'too many' in error_msg:
            dad_jokes = [
                "Whoa there, speed racer! Even my dad jokes need a breather. Try again in a moment!",
                "Easy there, tiger! You're clicking faster than my dad can tell a punchline. Slow down!",
                "Hold your horses! You're moving faster than a dad running to turn off the thermostat!",
                "Pump the brakes! Even the internet needs a coffee break. Try again soon!",
                "Woah! You're scrolling faster than dad jokes spread at a BBQ. Give it a sec!",
                "Cool your jets! You're browsing faster than dad running when mom says 'dinner's ready'!"
            ]
            import random
            return {
                "snippet": None, 
                "rate_limited": True, 
                "message": random.choice(dad_jokes)
            }
        print(f"Error fetching snippet: {e}")
    
    return {"snippet": content.description or None, "rate_limited": False}

@router.get("/related/{content_id}")
async def get_related_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get related content items for a given content ID.
    Returns stories from different sources about the same topic.
    """
    related_items = await deduplication_service.get_related_content(db, content_id)
    
    return {
        "related_items": [
            {
                "content_id": item.id,
                "title": item.title,
                "description": item.description,
                "category": item.category,
                "source_urls": item.source_urls,
                "source": item.source_metadata.get('source', 'Unknown') if item.source_metadata else 'Unknown',
                "picture_url": item.source_metadata.get('picture_url') if item.source_metadata else None,
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            for item in related_items
        ]
    }

@router.get("/article/{content_id}")
async def get_article_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch and return the full article content for a content item.
    For news articles: scrapes the article from the source URL
    For search queries: scrapes search results to provide context
    Returns content along with related items.
    """
    # Get content item from database
    result = await db.execute(
        select(ContentItem).where(ContentItem.id == content_id)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Get the source URL
    if not content.source_urls or len(content.source_urls) == 0:
        raise HTTPException(status_code=404, detail="No source URL available")
    
    source_url = content.source_urls[0]
    
    # Check if URL is actually a search query (not just trending_analysis type)
    is_search_url = ('duckduckgo.com' in source_url or 
                     'google.com/search' in source_url or
                     'bing.com/search' in source_url)
    
    # Scrape appropriate content based on actual URL type
    if is_search_url:
        article_data = await article_scraper.fetch_search_context(source_url)
    else:
        # For trending_analysis with news URLs, scrape as regular article
        article_data = await article_scraper.fetch_article(source_url)
    
    if not article_data:
        raise HTTPException(
            status_code=404, 
            detail="Unable to fetch content from source"
        )
    
    # Save scraped content back to database for future use
    try:
        content.content_text = article_data.get('content', '')[:10000]  # Limit to 10k chars
        
        # Update title if better one was scraped
        if article_data.get('title') and len(article_data['title']) > len(content.title or ''):
            content.title = article_data['title'][:500]
        
        # Save image URL if found
        if article_data.get('image_url'):
            if not content.source_metadata:
                content.source_metadata = {}
            content.source_metadata['picture_url'] = article_data['image_url']
            content.source_metadata['scraped_at'] = datetime.utcnow().isoformat()
        
        await db.commit()
        print(f"✅ Saved scraped content for item {content_id}")
    except Exception as e:
        print(f"⚠️ Error saving scraped content: {e}")
        await db.rollback()
    
    # Find related content items (after scraping succeeds)
    try:
        from sqlalchemy import or_, and_, func
        related_items = await find_related_content(db, content)
    except Exception as e:
        print(f"❌ Error finding related content: {e}")
        related_items = []
    
    # Add related items to response
    article_data['related_items'] = [
        {
            'content_id': item.id,
            'title': item.title,
            'description': item.description,
            'category': item.category,
            'tags': item.tags,
            'source_urls': item.source_urls,
            'source': item.source_metadata.get('source', 'Unknown') if item.source_metadata else 'Unknown',
            'created_at': item.created_at.isoformat() if item.created_at else None
        }
        for item in related_items
    ]
    
    return article_data


async def find_related_content(db: AsyncSession, content: ContentItem, limit: int = 5) -> List[ContentItem]:
    """
    Find related content items based on title similarity, tags, and keywords.
    For news articles: find related trending searches
    For trending searches: find related news articles
    """
    from sqlalchemy import or_, and_, func
    
    # Extract keywords from title (proper nouns - capitalized words)
    original_words = content.title.split()
    proper_nouns = [word.strip('.,!?:;"\'-()[]{}').lower() 
                    for word in original_words 
                    if word and word[0].isupper()]
    
    # Also extract other significant words (length > 2)
    other_keywords = [word.strip('.,!?:;"\'-()[]{}').lower() 
                      for word in original_words 
                      if len(word) > 2 and not word[0].isupper()]
    
    # Combine and filter stop words
    stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'their', 'called', 'begging'}
    all_keywords = [w for w in (proper_nouns + other_keywords) if w not in stop_words]
    
    # Prioritize proper nouns
    priority_keywords = proper_nouns[:8] if proper_nouns else all_keywords[:8]
    
    if not priority_keywords:
        return []
    
    print(f"🔍 Finding related content for '{content.title}' using keywords: {priority_keywords}")
    
    # Build query with OR conditions for each keyword
    conditions = []
    for keyword in priority_keywords:
        conditions.append(func.lower(ContentItem.title).contains(keyword))
        if content.description:
            conditions.append(func.lower(ContentItem.description).contains(keyword))
    
    # Execute query
    result = await db.execute(
        select(ContentItem).where(
            and_(
                ContentItem.id != content.id,
                ContentItem.is_published == True,
                or_(*conditions)
            )
        ).limit(limit * 2)  # Get more than needed for scoring
    )
    
    candidates = result.scalars().all()
    
    # Score each match
    scored_matches = []
    for item in candidates:
        score = 0
        item_title_lower = item.title.lower() if item.title else ''
        item_desc_lower = item.description.lower() if item.description else ''
        
        # Score based on keyword matches
        for keyword in proper_nouns:
            if keyword in item_title_lower:
                score += 2  # Proper noun match in title
            if keyword in item_desc_lower:
                score += 1  # Proper noun match in description
        
        for keyword in other_keywords:
            if keyword in item_title_lower or keyword in item_desc_lower:
                score += 1
        
        # Bonus for different source (news + search query pairing)
        if content.source_metadata and item.source_metadata:
            content_source = content.source_metadata.get('source', '')
            item_source = item.source_metadata.get('source', '')
            if content_source != item_source:
                score += 3
        
        # Bonus for different types (news article + pytrends query)
        has_pytrends = 'pytrends' in (item.tags or [])
        content_has_pytrends = 'pytrends' in (content.tags or [])
        if has_pytrends != content_has_pytrends:
            score += 5
        
        if score > 0:
            scored_matches.append((score, item))
    
    # Sort by score and return top matches
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    related = [item for score, item in scored_matches[:limit]]
    
    print(f"✅ Found {len(related)} related items")
    return related

@router.get("/topic/{topic_id}")
async def get_content_by_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get all content for a specific topic"""
    result = await db.execute(
        select(ContentItem).where(ContentItem.topic_id == topic_id)
    )
    content_items = result.scalars().all()
    return content_items
