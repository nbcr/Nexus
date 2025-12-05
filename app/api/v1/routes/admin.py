"""
Admin API Routes

Secure admin-only endpoints for:
- User management
- Interest tracking analytics
- Global and per-user settings management
- System monitoring

Security: All endpoints require admin authentication
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.api.v1.deps import get_db, get_current_user
from app.models import User, UserInteraction, ContentItem, UserSession
from app.core.config import settings

router = APIRouter()


# Pydantic Models
class GlobalSettings(BaseModel):
    minHoverDuration: int = 1500
    afkThreshold: int = 5000
    movementThreshold: int = 5
    microMovementThreshold: int = 20
    slowdownVelocityThreshold: float = 0.3
    velocitySampleRate: int = 100
    interestScoreThreshold: int = 50
    scrollSlowdownThreshold: float = 2.0


class UserCustomSettings(BaseModel):
    debug_mode: bool = False
    custom_settings: Optional[Dict[str, Any]] = None


# Admin verification dependency
def verify_admin(current_user: User = Depends(get_current_user)):
    """Verify that the current user is an admin"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/verify")
async def verify_admin_access(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify admin access and return user info"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "is_admin": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
    }


@router.get("/tracking-log")
async def get_tracking_log(
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get recent interest tracking events"""

    # Get recent interest tracking interactions
    result = await db.execute(
        select(UserInteraction)
        .where(
            UserInteraction.interaction_type.in_(
                ["interest_high", "interest_medium", "interest_low"]
            )
        )
        .order_by(UserInteraction.created_at.desc())
        .limit(limit)
    )

    interactions = result.scalars().all()

    events = []
    for interaction in interactions:
        events.append(
            {
                "id": interaction.id,
                "user_id": interaction.user_id,
                "session_id": interaction.session_id,
                "content_item_id": interaction.content_item_id,
                "interaction_type": interaction.interaction_type,
                "duration_seconds": interaction.duration_seconds,
                "created_at": interaction.created_at.isoformat(),
                "metadata": {},  # Metadata will be available when we add the column
            }
        )

    return {"events": events}


@router.post("/clear-tracking")
async def clear_tracking_log(
    admin: User = Depends(verify_admin), db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Clear all interest tracking data (destructive operation)"""

    # Delete interest tracking interactions
    result = await db.execute(
        select(UserInteraction).where(
            UserInteraction.interaction_type.in_(
                ["interest_high", "interest_medium", "interest_low"]
            )
        )
    )
    interactions = result.scalars().all()

    for interaction in interactions:
        await db.delete(interaction)

    await db.commit()

    return {"status": "cleared", "count": len(interactions)}


@router.get("/settings/global")
async def get_global_settings(admin: User = Depends(verify_admin)) -> Dict[str, Any]:
    """Get current global hover tracking settings"""

    # For now, return defaults. In production, these would be stored in database
    return {
        "minHoverDuration": 1500,
        "afkThreshold": 5000,
        "movementThreshold": 5,
        "microMovementThreshold": 20,
        "slowdownVelocityThreshold": 0.3,
        "velocitySampleRate": 100,
        "interestScoreThreshold": 50,
        "scrollSlowdownThreshold": 2.0,
    }


@router.post("/settings/global")
async def save_global_settings(
    settings: GlobalSettings,
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Save global hover tracking settings"""

    # TODO: Store in database (create settings table)
    # For now, just validate and return success

    return {"status": "saved", "message": "Global settings updated successfully"}


@router.get("/users")
async def get_all_users(
    admin: User = Depends(verify_admin), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get all users with interaction counts"""

    # Get all users
    result = await db.execute(select(User))
    users = result.scalars().all()

    user_list = []
    for user in users:
        # Count interactions
        interaction_count_result = await db.execute(
            select(func.count(UserInteraction.id)).where(
                UserInteraction.user_id == user.id
            )
        )
        interaction_count = interaction_count_result.scalar() or 0

        user_list.append(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "interaction_count": interaction_count,
                "debug_mode": getattr(user, "debug_mode", False),
                "custom_settings": None,  # TODO: Load from settings table
            }
        )

    return {"users": user_list}


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed information about a specific user"""

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get interaction stats
    total_result = await db.execute(
        select(func.count(UserInteraction.id)).where(UserInteraction.user_id == user_id)
    )
    total_interactions = total_result.scalar() or 0

    high_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.user_id == user_id,
                UserInteraction.interaction_type == "interest_high",
            )
        )
    )
    high_interest = high_result.scalar() or 0

    avg_duration_result = await db.execute(
        select(func.avg(UserInteraction.duration_seconds)).where(
            UserInteraction.user_id == user_id
        )
    )
    avg_duration = avg_duration_result.scalar() or 0

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "debug_mode": getattr(user, "debug_mode", False),
        "custom_settings": None,  # TODO: Load from settings table
        "stats": {
            "total_interactions": total_interactions,
            "high_interest": high_interest,
            "avg_duration": round(float(avg_duration), 1) if avg_duration else 0,
        },
    }


@router.post("/users/{user_id}/settings")
async def save_user_settings(
    user_id: int,
    settings: UserCustomSettings,
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Save custom settings for a specific user"""

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update debug mode
    user.debug_mode = settings.debug_mode

    # TODO: Store custom_settings in user_settings table

    await db.commit()

    return {"status": "saved", "message": f"Settings updated for user {user_id}"}


@router.get("/analytics")
async def get_analytics(
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get analytics data for specified date range"""

    try:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end) + timedelta(days=1)  # Include end date
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Interest distribution
    high_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.interaction_type == "interest_high",
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    high_count = high_result.scalar() or 0

    medium_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.interaction_type == "interest_medium",
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    medium_count = medium_result.scalar() or 0

    low_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.interaction_type == "interest_low",
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    low_count = low_result.scalar() or 0

    # Top content
    top_content_result = await db.execute(
        select(
            ContentItem.id,
            ContentItem.title,
            func.count(UserInteraction.id).label("view_count"),
        )
        .join(UserInteraction, ContentItem.id == UserInteraction.content_item_id)
        .where(
            and_(
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
        .group_by(ContentItem.id, ContentItem.title)
        .order_by(func.count(UserInteraction.id).desc())
        .limit(10)
    )

    top_content = []
    for row in top_content_result:
        top_content.append(
            {
                "content_id": row[0],
                "title": row[1],
                "view_count": row[2],
                "avg_score": 0,  # TODO: Calculate from metadata when available
            }
        )

    # Hover patterns
    avg_duration_result = await db.execute(
        select(func.avg(UserInteraction.duration_seconds)).where(
            and_(
                UserInteraction.interaction_type.in_(
                    ["interest_high", "interest_medium", "interest_low"]
                ),
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    avg_duration = avg_duration_result.scalar() or 0

    return {
        "interest_distribution": {
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
        },
        "top_content": top_content,
        "hover_patterns": {
            "avg_duration": round(float(avg_duration), 1) if avg_duration else 0,
            "avg_slowdowns": 0,  # TODO: Calculate from metadata
            "movement_rate": 0,  # TODO: Calculate from metadata
            "afk_rate": 0,  # TODO: Calculate from metadata
        },
    }
