"""User-related models."""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    debug_mode = Column(Boolean, default=False)
    must_reset_password = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    sessions = relationship("UserSession", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")
    interest_profile = relationship(
        "UserInterestProfile", back_populates="user", uselist=False
    )
    view_history = relationship("ContentViewHistory", back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # NULL for anonymous
    session_token = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    last_activity = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="sessions")
    interactions = relationship("UserInteraction", back_populates="session")


class ContentViewHistory(Base):
    """Track what content users have viewed and clicked."""

    __tablename__ = "content_view_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # NULL for anonymous
    session_token = Column(
        String(255), index=True, nullable=True
    )  # For anonymous tracking
    content_id = Column(
        Integer, ForeignKey("content_items.id"), nullable=False, index=True
    )
    content_slug = Column(
        String(255), nullable=False, index=True
    )  # Denormalized for quick lookup
    view_type = Column(String(50), nullable=False)  # 'seen', 'clicked', 'read'
    viewed_at = Column(DateTime, default=func.now(), nullable=False)
    time_spent_seconds = Column(
        Integer, nullable=True
    )  # Optional: track engagement time

    user = relationship("User", back_populates="view_history")
    content_item = relationship("ContentItem", back_populates="view_history")


class BrevoEmailEvent(Base):
    """Track Brevo email events (bounces, complaints, invalid emails, etc.)."""

    __tablename__ = "brevo_email_events"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # 'invalid_email', 'bounce', 'complaint', 'unsubscribe', etc.
    event_data = Column(String(1000), nullable=True)  # Store full event JSON for debugging
    received_at = Column(DateTime, default=func.now(), nullable=False)
    checked_at = Column(DateTime, nullable=True)  # When the registration page last checked
