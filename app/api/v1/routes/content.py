"""
Content Router

This module handles content-related endpoints including:
- List all content items (with pagination)
- Get specific content item details
- List content items by topic
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Annotated

from app.database import AsyncSessionLocal
from app.models import ContentItem, Topic
from app.schemas import ContentItem as ContentItemSchema, ContentWithTopic

# Router Configuration
router = APIRouter()

# Dependencies
async def get_db() -> AsyncSession:
    """Dependency for database session management."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

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
    return result.scalars().all()