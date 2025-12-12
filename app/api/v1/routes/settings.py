"""
Settings API endpoint to serve hover tracker configuration to clients
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user
from app.models import User

router = APIRouter()


@router.get("/hover-tracker")
async def get_hover_tracker_settings(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get hover tracker settings for the current user.
    Returns custom settings if available, otherwise returns global defaults.
    Also returns debug_mode status.
    """

    # Check if user has debug mode enabled
    debug_mode = False
    if current_user:
        debug_mode = getattr(current_user, "debug_mode", False)

    # TODO: Implement user-specific settings storage in database
    # Currently using global defaults for all users

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
