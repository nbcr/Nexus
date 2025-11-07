"""Content-related models."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    content_type = Column(String(50))
    content_text = Column(Text)
    ai_model_used = Column(String(100))
    source_urls = Column(JSON)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    topic = relationship("Topic", back_populates="content_items")
    interactions = relationship("UserInteraction", back_populates="content_item")