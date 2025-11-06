from fastapi import APIRouter, HTTPException, Depends # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy import select # pyright: ignore[reportMissingImports]
from typing import List

from app.database import AsyncSessionLocal
from app.models import ContentItem, Topic
from app.schemas import ContentItem as ContentItemSchema, ContentWithTopic

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

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
