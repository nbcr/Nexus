"""
Trending Router

This module handles trending topics and content:
- Fetching and updating trending topics
- Retrieving current trends
- Getting trending content
- Enhanced trend data with analytics
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status, Body
from sqlalchemy import select, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.api.v1.deps import DbSession, CurrentUser
from app.services.trending_service import trending_service
from app.schemas import (
    Topic as TopicSchema,
    ContentWithTopic,
    TrendingResponse,
    EnhancedTrendResponse
)
from app.models import Topic, ContentItem, User

# Router Configuration
router = APIRouter()

@router.post(
    "/refresh-trends",
    response_model=List[TopicSchema],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Trends refreshed successfully"},
        500: {"description": "Failed to refresh trends"}
    }
)
async def refresh_trending_topics(
    background_tasks: BackgroundTasks,
    force: bool = Body(False, description="Force immediate refresh"),
    db: DbSession = None
) -> List[Topic]:
    """
    Fetch and save the latest trending topics.
    
    Can be run in background unless force=True.
    
    Args:
        background_tasks: FastAPI background tasks
        force: Whether to force immediate refresh
        db: Database session
        
    Returns:
        List of updated/saved topics
        
    Raises:
        HTTPException: If refresh fails
    """
    try:
        if not force:
            background_tasks.add_task(
                trending_service.save_trends_to_database,
                db
            )
            return []
            
        saved_topics = await trending_service.save_trends_to_database(db)
        if not saved_topics:
            print("Warning: No topics were saved or updated")
            
        return saved_topics
        
    except Exception as e:
        print(f"Error in refresh_trending_topics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh trends: {str(e)}"
        )

@router.get(
    "/current-trends",
    response_model=List[TopicSchema],
    responses={
        200: {"description": "List of current trending topics"},
        500: {"description": "Failed to fetch trends"}
    }
)
async def get_current_trends(
    limit: int = Query(20, ge=1, le=100),
    min_score: float = Query(0.5, ge=0.0, le=1.0),
    category: Optional[str] = Query(None),
    db: DbSession = None
) -> List[Topic]:
    """
    Get currently trending topics from database.
    
    Args:
        limit: Maximum number of topics to return
        min_score: Minimum trend score to include
        category: Optional category filter
        db: Database session
        
    Returns:
        List of trending topics
        
    Raises:
        HTTPException: If fetch fails
    """
    try:
        query = (
            select(Topic)
            .where(Topic.trend_score >= min_score)
        )
        
        if category:
            query = query.where(Topic.category == category)
            
        query = (
            query
            .order_by(Topic.trend_score.desc(), Topic.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}"
        )

@router.get(
    "/trending-content",
    response_model=List[ContentWithTopic],
    responses={
        200: {"description": "List of trending content items"},
        500: {"description": "Failed to fetch trending content"}
    }
)
async def get_trending_content(
    limit: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.5, ge=0.0, le=1.0),
    content_type: Optional[str] = Query(None),
    db: DbSession = None
) -> List[dict]:
    """
    Get content items for trending topics.
    
    Args:
        limit: Maximum number of items to return
        min_score: Minimum trend score to include
        content_type: Optional content type filter
        db: Database session
        
    Returns:
        List of content items with their topics
        
    Raises:
        HTTPException: If fetch fails
    """
    try:
        query = (
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(ContentItem.is_published == True)
            .where(Topic.trend_score >= min_score)
        )
        
        if content_type:
            query = query.where(ContentItem.content_type == content_type)
            
        query = (
            query
            .order_by(Topic.trend_score.desc(), ContentItem.created_at.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        
        content_items = []
        for content_item, topic in result:
            content_dict = ContentWithTopic.model_validate(content_item).model_dump()
            content_dict["topic"] = topic
            content_items.append(content_dict)
        
        return content_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trending content: {str(e)}"
        )

@router.get(
    "/enhanced-trends",
    response_model=List[EnhancedTrendResponse],
    responses={
        200: {"description": "Enhanced trend data with analytics"},
        500: {"description": "Failed to fetch enhanced trends"}
    }
)
async def get_enhanced_trends(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    include_historical: bool = Query(False, description="Include historical trend data"),
    timeframe: str = Query("24h", regex="^(24h|7d|30d)$", description="Timeframe for analytics"),
    db: DbSession = None,
    current_user: Optional[CurrentUser] = None
) -> List[Dict[str, Any]]:
    """
    Get trending topics with enhanced data (images, sources, analytics).
    
    Args:
        page: Page number for pagination
        page_size: Number of items per page
        include_historical: Whether to include historical trend data
        timeframe: Timeframe for analytics (24h, 7d, 30d)
        db: Database session
        current_user: Optional authenticated user for personalization
        
    Returns:
        List of enhanced trend data
        
    Raises:
        HTTPException: If fetch fails
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get base query for trends
        query = select(Topic).where(Topic.trend_score > 0)
        
        # Add user personalization if authenticated
        if current_user:
            # Join with user interactions to personalize
            pass
            
        # Execute paginated query
        result = await db.execute(
            query
            .order_by(Topic.trend_score.desc())
            .offset(offset)
            .limit(page_size)
        )
        topics = result.scalars().all()
        
        # Enhance topics with additional data
        enhanced_topics = []
        for topic in topics:
            enhanced = await trending_service.enhance_topic(
                db,
                topic,
                include_historical=include_historical,
                timeframe=timeframe
            )
            enhanced_topics.append(enhanced)
        
        return enhanced_topics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch enhanced trends: {str(e)}"
        )