from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import User, UserInterestProfile, UserInteraction
from app.core.auth import get_password_hash, verify_password
from app.schemas import UserCreate, UserPreferences, UserProfile, UserStats

async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def update_user_profile(db: AsyncSession, user_id: int, profile: UserProfile) -> User:
    """Update a user's extended profile information."""
    user = await db.get(User, user_id)
    if not user:
        return None
        
    # Update profile fields
    user_profile = await db.get(UserInterestProfile, user_id)
    if not user_profile:
        user_profile = UserInterestProfile(user_id=user_id)
        db.add(user_profile)
    
    user_profile.bio = profile.bio
    user_profile.avatar_url = profile.avatar_url
    user_profile.social_links = profile.social_links
    user_profile.expertise = profile.expertise
    
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_preferences(db: AsyncSession, user_id: int) -> UserPreferences:
    """Get a user's content preferences."""
    profile = await db.get(UserInterestProfile, user_id)
    if not profile:
        return UserPreferences(
            interests=[],
            preferred_categories=[],
            reading_preferences={}
        )
    
    return UserPreferences(
        interests=profile.interests,
        preferred_categories=profile.preferred_categories,
        reading_preferences=profile.reading_preferences
    )

async def get_user_stats(db: AsyncSession, user_id: int, timeframe: str) -> UserStats:
    """Get user activity statistics for the given timeframe."""
    # Calculate time range
    now = datetime.utcnow()
    if timeframe == "24h":
        start_time = now - timedelta(days=1)
    elif timeframe == "7d":
        start_time = now - timedelta(days=7)
    elif timeframe == "30d":
        start_time = now - timedelta(days=30)
    else:  # "all"
        start_time = datetime.min
    
    # Get interaction counts
    interactions_query = (
        select(
            func.count().label("total"),
            func.count().filter(UserInteraction.interaction_type == "view").label("views"),
            func.count().filter(UserInteraction.interaction_type == "follow").label("follows")
        )
        .where(
            UserInteraction.user_id == user_id,
            UserInteraction.created_at >= start_time
        )
    )
    result = await db.execute(interactions_query)
    counts = result.first()
    
    # Get category breakdown
    categories_query = (
        select(
            UserInteraction.category,
            func.count().label("count")
        )
        .where(
            UserInteraction.user_id == user_id,
            UserInteraction.created_at >= start_time
        )
        .group_by(UserInteraction.category)
        .order_by(func.count().desc())
        .limit(5)
    )
    category_result = await db.execute(categories_query)
    top_categories = {row.category: row.count for row in category_result}
    
    # Get daily activity counts
    daily_query = (
        select(
            func.date_trunc("day", UserInteraction.created_at).label("day"),
            func.count().label("count")
        )
        .where(
            UserInteraction.user_id == user_id,
            UserInteraction.created_at >= start_time
        )
        .group_by(func.date_trunc("day", UserInteraction.created_at))
        .order_by("day")
    )
    daily_result = await db.execute(daily_query)
    daily_activity = {str(row.day.date()): row.count for row in daily_result}
    
    # Calculate engagement score (views + 2*follows / days)
    days = (now - start_time).days or 1  # avoid division by zero
    engagement = (counts.views + 2 * counts.follows) / days
    
    return UserStats(
        total_interactions=counts.total,
        content_views=counts.views,
        topic_follows=counts.follows,
        average_engagement=engagement,
        favorite_categories=top_categories,
        activity_by_day=daily_activity
    )