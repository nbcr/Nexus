"""Content-related models."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"))
    title = Column(String(500))
    slug = Column(
        String(255), unique=True, index=True, nullable=False
    )  # Unique identifier for direct linking
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)
    content_type = Column(String(50))
    content_text = Column(Text)
    facts = Column(Text, nullable=True)  # Extracted key facts from scraped content
    ai_model_used = Column(String(100))
    source_urls = Column(JSON, default=list)
    source_metadata = Column(JSON, default=dict)
    local_image_path = Column(
        String(255), nullable=True
    )  # Path to locally stored optimized image
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    topic = relationship("Topic", back_populates="content_items")
    interactions = relationship("UserInteraction", back_populates="content_item")
    view_history = relationship("ContentViewHistory", back_populates="content_item")
