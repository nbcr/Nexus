from sqlalchemy import (  # type: ignore
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    JSON,
    Text,
    Index,
    UUID as PGUUID,
)
from sqlalchemy.orm import relationship  # type: ignore
from sqlalchemy.sql import func  # type: ignore
from datetime import datetime
import uuid
from app.db import Base


class User(Base):
    """User table - supports both anonymous and registered users"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anonymous_id = Column(
        PGUUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    email = Column(String(255), unique=True, nullable=True)  # For future auth
    username = Column(String(100), unique=True, nullable=True)
    is_anonymous = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    interactions = relationship(
        "UserInteraction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, anonymous_id={self.anonymous_id})>"


class UserSession(Base):
    """Track user sessions for analytics and personalization"""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_token = Column(
        PGUUID(as_uuid=True),
        unique=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (Index("idx_session_user_active", "user_id", "last_activity"),)


class Topic(Base):
    """Topics/subjects for content generation"""

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    normalized_title = Column(String(500), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Trend metrics
    trend_score = Column(Float, default=0.0)  # From Google Trends
    search_volume = Column(Integer, default=0)

    # Categorization
    category = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)

    # AI embedding for similarity matching (Phase 5)
    embedding_vector = Column(JSON, nullable=True)  # Store OpenAI embeddings

    # Relationships
    content_items = relationship(
        "ContentItem", back_populates="topic", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_topic_trend", "trend_score", postgresql_using="btree"),
    )


class ContentItem(Base):
    """Generated content pieces (summaries, deep dives, etc.)"""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )

    # Content type and data
    content_type = Column(
        String(50), nullable=False, index=True
    )  # 'summary', 'deep_dive', 'video', 'news', 'reddit_discussion'
    content_text = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)  # Formatted version

    # AI generation metadata
    ai_model_used = Column(String(100), nullable=True)  # e.g., 'gpt-4', 'gpt-3.5-turbo'
    generation_prompt = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Source information
    source_urls = Column(JSON, default=list)  # List of source URLs
    source_metadata = Column(JSON, default=dict)  # Additional source info

    # Quality metrics
    quality_score = Column(Float, nullable=True)  # AI-assessed quality (0-1)
    readability_score = Column(Float, nullable=True)

    # Engagement metrics (updated by user interactions)
    view_count = Column(Integer, default=0)
    read_count = Column(Integer, default=0)  # Deep engagement
    avg_dwell_time = Column(Float, default=0.0)  # Milliseconds
    avg_scroll_depth = Column(Float, default=0.0)  # Percentage

    # Status
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    topic = relationship("Topic", back_populates="content_items")
    interactions = relationship(
        "UserInteraction", back_populates="content_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_content_type_published", "content_type", "is_published", "created_at"
        ),
        Index("idx_content_engagement", "view_count", "read_count"),
    )


class UserInteraction(Base):
    """Track all user interactions for algorithm training"""

    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content_item_id = Column(
        Integer, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )

    # Interaction type
    interaction_type = Column(
        String(50), nullable=False, index=True
    )  # 'view', 'read_more', 'scroll_past', 'dwell', 'share', 'save'

    # Detailed metrics
    dwell_time_ms = Column(Integer, default=0)  # How long content was visible
    scroll_depth_percent = Column(Float, default=0.0)  # 0-100
    scroll_velocity = Column(Float, nullable=True)  # Pixels per second

    # Viewport information
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)

    # Device information
    device_type = Column(String(50), nullable=True)  # 'mobile', 'tablet', 'desktop'

    # Computed engagement score (for algorithm)
    engagement_score = Column(Float, default=0.0)  # Weighted score 0-1

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Additional metadata
    interaction_metadata = Column("metadata", JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="interactions")
    content_item = relationship("ContentItem", back_populates="interactions")

    __table_args__ = (
        Index("idx_interaction_user_time", "user_id", "timestamp"),
        Index("idx_interaction_content_type", "content_item_id", "interaction_type"),
        Index("idx_interaction_engagement", "user_id", "engagement_score"),
    )


class UserInterestProfile(Base):
    """Aggregated user interest profile for recommendation algorithm"""

    __tablename__ = "user_interest_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Interest vector (computed from interactions)
    interest_topics = Column(JSON, default=dict)  # {topic_id: score}
    interest_categories = Column(JSON, default=dict)  # {category: score}
    interest_content_types = Column(JSON, default=dict)  # {type: preference}

    # Behavioral patterns
    avg_session_duration = Column(Float, default=0.0)
    preferred_content_length = Column(
        String(50), nullable=True
    )  # 'short', 'medium', 'long'
    peak_activity_hours = Column(JSON, default=list)  # List of hours (0-23)

    # Engagement metrics
    total_interactions = Column(Integer, default=0)
    total_read_time = Column(Integer, default=0)  # Milliseconds

    # Last updated
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (Index("idx_profile_user", "user_id"),)
