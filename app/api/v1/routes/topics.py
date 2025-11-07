"""
Topics Router

This module handles topic management endpoints:
- List all topics
- Get specific topic details
- Create new topics
- Get content associated with topics
"""
from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlalchemy import select
from typing import List, Optional, Dict, Any

from app.api.v1.deps import DbSession
from app.models import Topic, ContentItem
from app.schemas import (
    Topic as TopicSchema,
    TopicWithContent,
    TopicCreate,
    ContentItem as ContentItemSchema
)

# Router Configuration
router = APIRouter()

@router.get(
    "/",
    response_model=List[TopicSchema],
    responses={
        200: {
            "description": "List of topics",
            "content": {
                "application/json": {
                    "example": [{
                        "id": 1,
                        "title": "AI in Healthcare",
                        "trend_score": 0.85
                    }]
                }
            }
        }
    }
)
async def get_topics(
    skip: int = Query(0, ge=0, description="Number of topics to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of topics to return"),
    category: Optional[str] = Query(None, description="Filter topics by category"),
    min_trend_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum trend score"),
    db: DbSession = None
) -> List[Topic]:
    """
    Get all topics with optional filtering and pagination.
    
    Args:
        skip: Number of topics to skip (pagination offset)
        limit: Maximum number of topics to return
        category: Optional category filter
        min_trend_score: Optional minimum trend score filter
        db: Database session
        
    Returns:
        List of topics matching the criteria
    """
    query = select(Topic)
    
    if category:
        query = query.where(Topic.category == category)
    if min_trend_score is not None:
        query = query.where(Topic.trend_score >= min_trend_score)
    
    query = query.order_by(Topic.trend_score.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all()

@router.get(
    "/{topic_id}",
    response_model=TopicWithContent,
    responses={
        200: {"description": "Topic details with content"},
        404: {"description": "Topic not found"}
    }
)
async def get_topic(
    topic_id: int = Path(..., ge=1),
    include_unpublished: bool = Query(False, description="Include unpublished content items"),
    db: DbSession = None
) -> Topic:
    """
    Get a specific topic with its associated content.
    
    Args:
        topic_id: ID of the topic to retrieve
        include_unpublished: Whether to include unpublished content
        db: Database session
        
    Returns:
        Topic with its content
        
    Raises:
        HTTPException: If topic is not found
    """
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id)
    )
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )
    
    # Filter content items if needed
    if not include_unpublished:
        topic.content_items = [
            item for item in topic.content_items
            if item.is_published
        ]
    
    return topic

@router.post(
    "/",
    response_model=TopicSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Topic created successfully"},
        400: {"description": "Invalid topic data"}
    }
)
async def create_topic(
    topic_data: TopicCreate,
    db: DbSession
) -> Topic:
    """
    Create a new topic.
    
    Args:
        topic_data: Topic creation data
        db: Database session
        
    Returns:
        Created topic
        
    Raises:
        HTTPException: If topic already exists
    """
    # Check if topic with same title exists
    existing = await db.execute(
        select(Topic).where(Topic.normalized_title == topic_data.title.lower().replace(" ", "_"))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic with this title already exists"
        )
    
    topic = Topic(
        title=topic_data.title,
        normalized_title=topic_data.title.lower().replace(" ", "_"),
        description=topic_data.description,
        category=topic_data.category,
        trend_score=topic_data.trend_score or 0.0,
        tags=topic_data.tags or []
    )
    
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    
    return topic

@router.get(
    "/{topic_id}/content",
    response_model=List[ContentItemSchema],
    responses={
        200: {"description": "List of content items for the topic"},
        404: {"description": "Topic not found"}
    }
)
async def get_topic_content(
    topic_id: int = Path(..., ge=1),
    include_unpublished: bool = Query(False, description="Include unpublished content items"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = None
) -> List[ContentItem]:
    """
    Get content items for a specific topic.
    
    Args:
        topic_id: ID of the topic to get content for
        include_unpublished: Whether to include unpublished content
        skip: Number of items to skip
        limit: Maximum number of items to return
        db: Database session
        
    Returns:
        List of content items for the topic
        
    Raises:
        HTTPException: If topic is not found
    """
    # Verify topic exists
    topic_exists = await db.execute(
        select(Topic.id).where(Topic.id == topic_id)
    )
    if not topic_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {topic_id} not found"
        )
    
    # Build query
    query = select(ContentItem).where(ContentItem.topic_id == topic_id)
    
    if not include_unpublished:
        query = query.where(ContentItem.is_published == True)
    
    query = query.order_by(ContentItem.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all()