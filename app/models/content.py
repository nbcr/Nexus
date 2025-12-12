"""Content-related models."""

from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
    LargeBinary,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id"))
    title: Mapped[str] = mapped_column(String(500))
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )  # Unique identifier for direct linking
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[List[Any]] = mapped_column(JSON, default=list)
    content_type: Mapped[str] = mapped_column(String(50))
    content_text: Mapped[str] = mapped_column(Text)
    facts: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # Extracted key facts from scraped content
    ai_model_used: Mapped[str] = mapped_column(String(100))
    source_urls: Mapped[List[str]] = mapped_column(JSON, default=list)
    source_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    image_data: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )  # WebP image stored as binary
    local_image_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Path to locally stored optimized image
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    topic = relationship("Topic", back_populates="content_items")
    interactions = relationship("UserInteraction", back_populates="content_item")
    view_history = relationship("ContentViewHistory", back_populates="content_item")
