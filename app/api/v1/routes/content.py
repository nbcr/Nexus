"""
Content Router

This module handles content-related endpoints including:
- Personalized infinite scroll feed
- List all content items (with pagination)
- Get specific content item details
- List content items by topic
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Annotated, Optional

from app.database import AsyncSessionLocal
from app.models import ContentItem, Topic, User
from app.schemas import ContentItem as ContentItemSchema, ContentWithTopic
from app.services.content_recommendation import recommendation_service
from app.services.article_scraper import article_scraper
from app.api.v1.deps import get_db, get_current_user

# Router Configuration
router = APIRouter()

@router.get(
    "/feed",
    responses={
        200: {"description": "Personalized content feed"},
        400: {"description": "Invalid pagination parameters"}
    }
)
async def get_personalized_feed(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    category: Optional[str] = Query(None, description="Filter by category"),
    exclude_ids: Optional[str] = Query(None, description="Comma-separated list of content IDs to exclude"),
    current_user: Optional[User] = Depends(get_current_user),
    nexus_session: Optional[str] = Cookie(default=None)
):
    """
    Get personalized content feed with infinite scroll support.
    
    This endpoint provides:
    - Personalized recommendations based on user history
    - Trending content from Google Trends
    - Category filtering
    - Infinite scroll pagination
    - Exclusion of already-viewed content
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 50)
        category: Optional category filter
        exclude_ids: Comma-separated list of content IDs already displayed
        current_user: Authenticated user (optional)
        nexus_session: Anonymous session cookie (optional)
        db: Database session
        
    Returns:
        List of content items with relevance scores
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
    user_id = current_user.id if current_user else None
    
    # Get personalized feed
    if category:
        # If filtering by category, use trending feed
        feed_items = await recommendation_service.get_trending_feed(
            db=db,
            page=page,
            page_size=page_size,
            category=category,
            exclude_ids=excluded_ids
        )
    else:
        # Use personalized feed
        feed_items = await recommendation_service.get_personalized_feed(
            db=db,
            user_id=user_id,
            session_token=session_token,
            page=page,
            page_size=page_size,
            exclude_ids=excluded_ids
        )
    
    return {
        "page": page,
        "page_size": page_size,
        "items": feed_items,
        "has_more": len(feed_items) == page_size,
        "is_personalized": user_id is not None or session_token is not None
    }

@router.get(
    "/trending-feed",
    responses={
        200: {"description": "Trending content feed"},
        400: {"description": "Invalid pagination parameters"}
    }
)
async def get_trending_feed_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    category: Optional[str] = Query(None, description="Filter by category"),
    exclude_ids: Optional[str] = Query(None, description="Comma-separated list of content IDs to exclude")
):
    """
    Get trending content feed (non-personalized).
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 50)
        category: Optional category filter
        exclude_ids: Comma-separated list of content IDs already displayed
        db: Database session
        
    Returns:
        List of trending content items
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


@router.get(
    "/",
    response_model=List[ContentWithTopic],
    responses={
        200: {"description": "List of content items with their topics"},
        400: {"description": "Invalid pagination parameters"}
    }
)
async def get_content_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> List[dict]:
    """
    Get a paginated list of content items with their associated topics.
    
    Args:
        skip: Number of items to skip (pagination offset)
        limit: Maximum number of items to return
        db: Database session dependency
        
    Returns:
        List of content items with their topics
    """
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .offset(skip)
        .limit(limit)
    )
    
    content_items = []
    for content_item, topic in result:
        content_dict = ContentItemSchema.model_validate(content_item).model_dump()
        content_dict["topic"] = topic
        content_items.append(content_dict)
    
    return content_items

@router.get(
    "/{content_id}",
    response_model=ContentWithTopic,
    responses={
        200: {"description": "Content item details"},
        404: {"description": "Content item not found"}
    }
)
async def get_content_item(
    content_id: Annotated[int, Path(ge=1)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> dict:
    """
    Get a specific content item by its ID.
    
    Args:
        content_id: ID of the content item to retrieve
        db: Database session dependency
        
    Returns:
        Content item with its topic
        
    Raises:
        HTTPException: If content item is not found
    """
    result = await db.execute(
        select(ContentItem, Topic)
        .join(Topic, ContentItem.topic_id == Topic.id)
        .where(ContentItem.id == content_id)
    )
    
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Content item with id {content_id} not found"
        )
    
    content_item, topic = row
    content_dict = ContentItemSchema.model_validate(content_item).model_dump()
    content_dict["topic"] = topic
    
    return content_dict

@router.get(
    "/topic/{topic_id}",
    response_model=List[ContentItemSchema],
    responses={
        200: {"description": "List of content items for the topic"},
        404: {"description": "Topic not found"}
    }
)
async def get_content_by_topic(
    topic_id: Annotated[int, Path(ge=1)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> List[ContentItem]:
    """
    Get all content items for a specific topic.
    
    Args:
        topic_id: ID of the topic to get content for
        skip: Number of items to skip (pagination offset)
        limit: Maximum number of items to return
        db: Database session dependency
        
    Returns:
        List of content items for the topic
        
    Raises:
        HTTPException: If topic is not found
    """
    # First check if topic exists
    topic = await db.execute(select(Topic).where(Topic.id == topic_id))
    if not topic.scalar_one_or_none():
        raise HTTPException(
            status_code=404,
            detail=f"Topic with id {topic_id} not found"
        )
    
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.topic_id == topic_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()@router.get(
    "/article/{content_id}",
    responses={
        200: {"description": "Article content retrieved"},
        404: {"description": "Content not found or article unavailable"}
    }
)
async def get_article_content(
    content_id: int = Path(..., ge=1, description="Content ID"),
    db: AsyncSession = Depends(get_db)
):
    '''
    Fetch and return the full article content for a content item.
    
    Scrapes the article from the source URL and returns readable content.
    
    Args:
        content_id: ID of the content item
        db: Database session
        
    Returns:
        Dict with article title, content, author, date, and image
        
    Raises:
        HTTPException: If content not found or scraping fails
    '''
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
    
    # Scrape the article
    article_data = await article_scraper.fetch_article(source_url)
    
    if not article_data:
        raise HTTPException(
            status_code=404, 
            detail="Unable to fetch article content from source"
        )
    
    return article_data
