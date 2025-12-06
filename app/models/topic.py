"""Topic-related models."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), unique=True, index=True)
    normalized_title = Column(String(500), unique=True, index=True)
    description = Column(Text)
    trend_score = Column(Float, default=0.0)
    category = Column(String(100))
    tags = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    content_items = relationship("ContentItem", back_populates="topic")
