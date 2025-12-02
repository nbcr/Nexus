import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession  # pyright: ignore[reportMissingImports]
from sqlalchemy import select  # pyright: ignore[reportMissingImports]
from app.models import UserSession, UserInteraction, ContentItem
from app.core.config import settings


async def create_anonymous_session(db: AsyncSession, session_token: str = None):
    """Create or get an anonymous user session"""
    if not session_token:
        session_token = str(uuid.uuid4())

    # Check if session exists
    result = await db.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one_or_none()

    if not session:
        # Create new anonymous session (user_id is NULL for anonymous users)
        session = UserSession(
            session_token=session_token,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),  # 30-day session
            last_activity=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    return session


async def track_content_interaction(
    db: AsyncSession,
    session_token: str,
    content_item_id: int,
    interaction_type: str = "view",
    duration_seconds: int = 0,
    metadata: dict = None,
):
    """Track user interaction with content (works for both anonymous and registered users)

    Args:
        db: Database session
        session_token: Session identifier
        content_item_id: ID of the content item
        interaction_type: Type of interaction (view, click, interest_high, etc.)
        duration_seconds: Duration of interaction in seconds
        metadata: Optional metadata dict (currently logged but not stored in DB)
    """
    # Get or create session
    session = await create_anonymous_session(db, session_token)

    # Update last activity
    session.last_activity = datetime.utcnow()

    # Record interaction
    interaction = UserInteraction(
        user_id=None,  # NULL for anonymous users
        session_id=session.id,  # Link to session for anonymous users
        content_item_id=content_item_id,
        interaction_type=interaction_type,
        duration_seconds=duration_seconds,
        created_at=datetime.utcnow(),
    )

    # Log metadata for future analysis (not stored in DB yet)
    if metadata:
        print(f"Interest tracking metadata for content {content_item_id}: {metadata}")

    db.add(interaction)
    await db.commit()

    return interaction


async def get_session_history(db: AsyncSession, session_token: str):
    """Get content history for a session"""
    result = await db.execute(
        select(UserInteraction, ContentItem)
        .join(ContentItem, UserInteraction.content_item_id == ContentItem.id)
        .join(UserSession, UserInteraction.session_id == UserSession.id)
        .where(UserSession.session_token == session_token)
        .order_by(UserInteraction.created_at.desc())
    )

    history = []
    for interaction, content in result:
        history.append(
            {
                "content": content,
                "interaction_type": interaction.interaction_type,
                "viewed_at": interaction.created_at,
                "duration_seconds": interaction.duration_seconds,
            }
        )

    return history


async def migrate_session_to_user(db: AsyncSession, session_token: str, user_id: int):
    """Migrate anonymous session history to a registered user"""
    # Update all interactions from this session to belong to the user
    result = await db.execute(
        select(UserInteraction)
        .join(UserSession, UserInteraction.session_id == UserSession.id)
        .where(UserSession.session_token == session_token)
        .where(UserInteraction.user_id.is_(None))
    )

    interactions = result.scalars().all()

    for interaction in interactions:
        interaction.user_id = user_id
        interaction.session_id = (
            None  # Remove session link since user is now registered
        )

    await db.commit()

    return len(interactions)


async def update_interaction_duration(
    db: AsyncSession, session_token: str, content_item_id: int, duration_seconds: int
):
    """Update the duration of the most recent interaction for this content"""
    # Get the session
    session_result = await db.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        return None

    # Find the most recent interaction for this content in this session
    interaction_result = await db.execute(
        select(UserInteraction)
        .where(UserInteraction.session_id == session.id)
        .where(UserInteraction.content_item_id == content_item_id)
        .order_by(UserInteraction.created_at.desc())
        .limit(1)
    )

    interaction = interaction_result.scalar_one_or_none()

    if interaction:
        interaction.duration_seconds = duration_seconds
        await db.commit()
        await db.refresh(interaction)
        return interaction

    return None
