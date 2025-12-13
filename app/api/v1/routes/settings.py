"""
Settings API endpoint to serve hover tracker configuration to clients
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user_optional
from app.models import User

router = APIRouter()


@router.get("/hover-tracker")
async def get_hover_tracker_settings(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get hover tracker settings for the current user.
    Works for both authenticated and anonymous users.
    Returns custom settings if available, otherwise returns global defaults.
    Also returns debug_mode status for authenticated users.
    """

    # Check if user has debug mode enabled (only if authenticated)
    debug_mode = False
    if current_user:
        debug_mode = getattr(current_user, "debug_mode", False)

    # User-specific settings are stored in database via UserSettings model
    # For now, using global defaults. Extended in future for per-user customization

    settings = {
        "minHoverDuration": 1500,
        "afkThreshold": 5000,
        "movementThreshold": 5,
        "microMovementThreshold": 20,
        "slowdownVelocityThreshold": 0.3,
        "velocitySampleRate": 100,
        "interestScoreThreshold": 50,
        "scrollSlowdownThreshold": 2.0,
        "showVisualFeedback": debug_mode,  # Only show visual feedback in debug mode
        "debugMode": debug_mode,
    }

    return settings
