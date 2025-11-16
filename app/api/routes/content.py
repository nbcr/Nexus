from fastapi import APIRouter, HTTPException, Depends, Query, Request, Cookie # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # pyright: ignore[reportMissingImports]
from typing import List, Optional

from app.database import AsyncSessionLocal
from app.models import ContentItem, Topic
from app.schemas import ContentItem as ContentItemSchema, ContentWithTopic
from app.services.content_recommendation import recommendation_service

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
    
    # Get personalized feed
    if category:
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
        .offset(skip)
        .limit(limit)
    )
    
    content_items = []
    for content_item, topic in result:
        content_dict = ContentItemSchema.model_validate(content_item).model_dump()
        content_dict["topic"] = topic
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
    content_dict["topic"] = topic
    
    return content_dict

@router.get("/topic/{topic_id}")
async def get_content_by_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get all content for a specific topic"""
    result = await db.execute(
        select(ContentItem).where(ContentItem.topic_id == topic_id)
    )
    content_items = result.scalars().all()
    return content_items
