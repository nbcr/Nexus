from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # pyright: ignore[reportMissingImports]
from sqlalchemy import select, desc, func # type: ignore
from typing import List

from app.database import AsyncSessionLocal
from app.services.trending_service import trending_service
from app.schemas import Topic as TopicSchema, ContentWithTopic
from app.models import User

router = APIRouter()

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@router.post("/refresh-trends", response_model=List[TopicSchema])
async def refresh_trending_topics(
    db: AsyncSession = Depends(get_db)
):
    """Fetch and save the latest trending topics"""
    try:
        saved_topics = await trending_service.save_trends_to_database(db)
        
        if not saved_topics:
            return {"message": "No new trends found or all trends already exist"}
            
        return saved_topics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh trends: {str(e)}")

@router.get("/current-trends", response_model=List[TopicSchema])
async def get_current_trends(
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """Get currently trending topics from database"""
    from sqlalchemy import select # pyright: ignore[reportMissingImports]
    from app.models import Topic
    
    try:
        result = await db.execute(
            select(Topic)
            .where(Topic.trend_score >= 0.5)
            .order_by(Topic.trend_score.desc(), Topic.created_at.desc())
            .limit(limit)
        )
        topics = result.scalars().all()
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")

@router.get("/trending-content")
async def get_trending_content(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """Get content items for trending topics"""
    from sqlalchemy import select # type: ignore
    from app.models import ContentItem, Topic
    
    try:
        result = await db.execute(
            select(ContentItem, Topic)
            .join(Topic, ContentItem.topic_id == Topic.id)
            .where(ContentItem.is_published == True)
            .where(Topic.trend_score >= 0.5)
            .order_by(Topic.trend_score.desc(), ContentItem.created_at.desc())
            .limit(limit)
        )
        
        content_items = []
        for content_item, topic in result:
            content_dict = ContentWithTopic.model_validate(content_item).model_dump()
            content_dict["topic"] = topic
            content_items.append(content_dict)
        
        return content_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending content: {str(e)}")

@router.get("/enhanced-trends")
async def get_enhanced_trends(
    page: int = 1,
    page_size: int = 10,
    include_historical: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get trending topics with enhanced data (images, sources, etc.)
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        include_historical: Whether to include historical trends
    """
    try:
        # Fetch current trends
        current_trends = await trending_service.fetch_canada_trends()
        
        if include_historical:
            # Get historical trends from database
            from sqlalchemy import select, desc # pyright: ignore[reportMissingImports]
            from app.models import Topic
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Query historical topics
            result = await db.execute(
                select(Topic)
                .where(Topic.trend_score > 0)  # Only get trending topics
                .order_by(desc(Topic.created_at))
                .offset(offset)
                .limit(page_size)
            )
            
            historical_topics = result.scalars().all()
            
            # Count total historical topics for pagination
            total_count_result = await db.execute(
                select(func.count()).select_from(Topic).where(Topic.trend_score > 0)
            )
            total_count = total_count_result.scalar()
            
            # Combine current and historical trends
            all_trends = current_trends.copy()
            
            # Add historical trends that aren't in current trends
            current_titles = {trend['title'].lower() for trend in current_trends}
            for topic in historical_topics:
                if topic.title.lower() not in current_titles:
                    all_trends.append({
                        'title': topic.title,
                        'description': topic.description,
                        'category': topic.category,
                        'trend_score': topic.trend_score,
                        'tags': topic.tags,
                        'source': 'Historical',
                        'created_at': topic.created_at.isoformat(),
                        'news_items': []  # Historical items might not have news items
                    })
            
            # Apply pagination to combined results
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_trends = all_trends[start_idx:end_idx]
            
            return {
                "status": "success",
                "page": page,
                "page_size": page_size,
                "total_count": total_count + len(current_trends),
                "trends_count": len(paginated_trends),
                "has_more": end_idx < len(all_trends),
                "trends": paginated_trends
            }
        
        else:
            # Just return current trends with pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_trends = current_trends[start_idx:end_idx]
            
            return {
                "status": "success",
                "page": page,
                "page_size": page_size,
                "total_count": len(current_trends),
                "trends_count": len(paginated_trends),
                "has_more": end_idx < len(current_trends),
                "trends": paginated_trends
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch enhanced trends: {str(e)}")

@router.get("/test-feed")
async def test_feed():
    """Test the RSS feed connection"""
    try:
        trends = await trending_service.fetch_canada_trends()
        return {
            "status": "success",
            "trends_count": len(trends),
            "sample_trends": [{"title": t["title"], "source": t["source"], "has_image": bool(t["image_url"])} for t in trends[:3]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feed test failed: {str(e)}")
