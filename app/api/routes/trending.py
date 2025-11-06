from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # pyright: ignore[reportMissingImports]
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
async def get_enhanced_trends():
    """Get trending topics with enhanced data (images, sources, etc.)"""
    try:
        trends = await trending_service.fetch_canada_trends()
        return {
            "status": "success",
            "trends_count": len(trends),
            "trends": trends
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
