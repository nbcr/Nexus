from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    sessions = relationship("UserSession", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")
    interest_profile = relationship("UserInterestProfile", back_populates="user", uselist=False)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for anonymous
    session_token = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    last_activity = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="sessions")
    interactions = relationship("UserInteraction", back_populates="session")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), unique=True, index=True)
    normalized_title = Column(String(200), unique=True, index=True)
    description = Column(Text)
    trend_score = Column(Float, default=0.0)
    category = Column(String(100))
    tags = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    content_items = relationship("ContentItem", back_populates="topic")


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


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL for anonymous
    session_id = Column(Integer, ForeignKey("user_sessions.id"), nullable=True)  # Link to session
    content_item_id = Column(Integer, ForeignKey("content_items.id"))
    interaction_type = Column(String(50))
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="interactions")
    session = relationship("UserSession", back_populates="interactions")
    content_item = relationship("ContentItem", back_populates="interactions")


class UserInterestProfile(Base):
    __tablename__ = "user_interest_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    interests = Column(JSON)
    preferred_categories = Column(JSON)
    reading_preferences = Column(JSON)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="interest_profile")
