"""Interaction-related models."""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # NULL for anonymous
    session_id = Column(
        Integer, ForeignKey("user_sessions.id"), nullable=True
    )  # Link to session
    content_item_id = Column(Integer, ForeignKey("content_items.id"))
    interaction_type = Column(String(50))
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="interactions")
    session = relationship("UserSession", back_populates="interactions")
    content_item = relationship("ContentItem", back_populates="interactions")


class UserInterestProfile(Base):
    __tablename__ = "user_interest_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    interests = Column(JSON, default=list)
    preferred_categories = Column(JSON, default=list)
    reading_preferences = Column(JSON, default=dict)
    bio = Column(String(500), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    social_links = Column(JSON, default=dict)
    expertise = Column(JSON, default=list)
    last_updated = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="interest_profile")
