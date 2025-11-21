from fastapi import APIRouter, HTTPException, Depends # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # pyright: ignore[reportMissingImports]
from sqlalchemy import select # pyright: ignore[reportMissingImports]
from typing import List

from app.db import AsyncSessionLocal
from app.models import Topic, ContentItem
from app.schemas import Topic as TopicSchema, TopicWithContent

router = APIRouter()

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@router.get("/", response_model=List[TopicSchema])
async def get_topics(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get all topics with pagination"""
    result = await db.execute(select(Topic).offset(skip).limit(limit))
    topics = result.scalars().all()
    return topics

@router.get("/{topic_id}", response_model=TopicWithContent)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific topic with its content"""
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id)
    )
    topic = result.scalar_one_or_none()
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return topic

@router.post("/", response_model=TopicSchema)
async def create_topic(topic_data: dict, db: AsyncSession = Depends(get_db)):
    """Create a new topic"""
    # Simple create endpoint - we'll enhance this later
    topic = Topic(
        title=topic_data.get("title"),
        normalized_title=topic_data.get("title").lower().replace(" ", "_"),
        description=topic_data.get("description"),
        category=topic_data.get("category"),
        trend_score=topic_data.get("trend_score", 0.0),
        tags=topic_data.get("tags", [])
    )
    
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    
    return topic

@router.get("/{topic_id}/content")
async def get_topic_content(topic_id: int, db: AsyncSession = Depends(get_db)):
    """Get content for a specific topic"""
    result = await db.execute(
        select(ContentItem).where(ContentItem.topic_id == topic_id)
    )
    content_items = result.scalars().all()
    return content_items
