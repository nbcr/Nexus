"""
Session Router

This module handles user session management and content interaction tracking:
- Anonymous session creation and management
- Content view tracking
- Session history retrieval
- Session migration to registered users
"""
from fastapi import APIRouter, HTTPException, Request, Response, Path, Cookie, Depends, Body
from typing import Optional, Dict, List, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.v1.deps import get_db, get_current_user
from app.models import User
from app.services.session_service import (
    create_anonymous_session,
    track_content_interaction,
    get_session_history,
    migrate_session_to_user,
    update_interaction_duration
)
from app.schemas import ContentWithTopic, SessionResponse, HistoryResponse

class ViewDurationUpdate(BaseModel):
    duration_seconds: int

class InterestData(BaseModel):
    content_id: int
    interest_score: int
    hover_duration_ms: int
    movement_detected: bool
    slowdowns_detected: int
    clicks_detected: int
    was_afk: bool
    trigger: str
    timestamp: str

# Router Configuration
router = APIRouter()

# Session token management
def get_session_token(
    request: Request,
    nexus_session: Optional[str] = Cookie(default=None)
) -> str:
    """
    Get or create session token from cookies or headers.
    
    Args:
        request: FastAPI request object
        nexus_session: Session cookie if present
        
    Returns:
        str: Valid session token
    """
    # Try cookie first
    if nexus_session:
        return nexus_session
    
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Session "):
        return auth_header.replace("Session ", "")
    
    # Create new token if none exists
    return str(uuid.uuid4())

@router.post(
    "/track-view/{content_id}",
    response_model=Dict[str, str],
    responses={
        200: {"description": "View tracked successfully"},
        404: {"description": "Content not found"},
        500: {"description": "Tracking failed"}
    }
)
async def track_content_view(
    request: Request,
    response: Response,
    content_id: int = Path(..., ge=1, description="ID of the content being viewed"),
    duration_seconds: Optional[int] = Body(default=0, embed=True),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Track when a user views content.
    
    Sets a session cookie if one doesn't exist.
    
    Args:
        content_id: ID of the content being viewed
        duration_seconds: Optional duration the user spent viewing the content
        request: FastAPI request object
        response: FastAPI response object
        db: Database session
        
    Returns:
        dict: Status and session token
        
    Raises:
        HTTPException: If tracking fails
    """
    session_token = get_session_token(request)
    
    try:
        await track_content_interaction(
            db,
            session_token,
            content_id,
            interaction_type="view",
            duration_seconds=duration_seconds or 0
        )
        
        # Set session cookie
        response.set_cookie(
            key="nexus_session",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=2592000  # 30 days
        )
        
        return {"status": "tracked", "session_token": session_token}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tracking failed: {str(e)}"
        )

@router.post(
    "/track-interest",
    response_model=Dict[str, str],
    responses={
        200: {"description": "Interest tracked successfully"},
        500: {"description": "Tracking failed"}
    }
)
async def track_content_interest(
    request: Request,
    response: Response,
    interest_data: InterestData = Body(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Track user interest in content based on hover behavior.
    
    This endpoint receives detailed interaction data including:
    - Interest score calculated from hover patterns
    - Hover duration and movement detection
    - Slowdown detection (user reading carefully)
    - Click detection
    - AFK detection
    
    Args:
        interest_data: Detailed interest metrics
        request: FastAPI request object
        response: FastAPI response object
        db: Database session
        
    Returns:
        dict: Status message
        
    Raises:
        HTTPException: If tracking fails
    """
    session_token = get_session_token(request)
    
    try:
        # Track the interaction with additional metadata
        metadata = {
            "interest_score": interest_data.interest_score,
            "hover_duration_ms": interest_data.hover_duration_ms,
            "movement_detected": interest_data.movement_detected,
            "slowdowns_detected": interest_data.slowdowns_detected,
            "clicks_detected": interest_data.clicks_detected,
            "was_afk": interest_data.was_afk,
            "trigger": interest_data.trigger
        }
        
        # Determine interaction type based on interest level
        interaction_type = "interest_high" if interest_data.interest_score >= 70 else "interest_medium" if interest_data.interest_score >= 50 else "interest_low"
        
        await track_content_interaction(
            db,
            session_token,
            interest_data.content_id,
            interaction_type=interaction_type,
            duration_seconds=interest_data.hover_duration_ms // 1000,  # Convert to seconds
            metadata=metadata
        )
        
        # Set session cookie
        response.set_cookie(
            key="nexus_session",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=2592000  # 30 days
        )
        
        return {
            "status": "tracked",
            "interest_score": str(interest_data.interest_score),
            "interaction_type": interaction_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Interest tracking failed: {str(e)}"
        )

@router.put(
    "/update-duration/{content_id}",
    response_model=Dict[str, str],
    responses={
        200: {"description": "Duration updated successfully"},
        404: {"description": "Interaction not found"},
        500: {"description": "Update failed"}
    }
)
async def update_view_duration(
    request: Request,
    content_id: int = Path(..., ge=1, description="ID of the content"),
    duration_data: ViewDurationUpdate = Body(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Update the duration spent viewing content.
    
    This is called when the user scrolls away from a card or closes the page.
    
    Args:
        content_id: ID of the content
        duration_data: Duration in seconds
        request: FastAPI request object
        db: Database session
        
    Returns:
        dict: Status message
        
    Raises:
        HTTPException: If update fails
    """
    session_token = get_session_token(request)
    
    try:
        await update_interaction_duration(
            db,
            session_token,
            content_id,
            duration_data.duration_seconds
        )
        
        return {"status": "updated", "duration_seconds": str(duration_data.duration_seconds)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Duration update failed: {str(e)}"
        )

@router.get(
    "/history",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Session history retrieved"},
        500: {"description": "Failed to load history"}
    }
)
async def get_user_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get viewing history for current session.
    
    If user is authenticated, returns combined history.
    
    Args:
        request: FastAPI request object
        db: Database session
        current_user: Optional authenticated user
        
    Returns:
        dict: Session history and metadata
        
    Raises:
        HTTPException: If history retrieval fails
    """
    session_token = get_session_token(request)
    
    try:
        history = await get_session_history(db, session_token)
        return history, {
            "is_anonymous": current_user is None
        }
        
        if current_user is None:
            response["warning"] = (
                "Your history is stored with a session cookie. "
                "Clear your cookies and you'll lose this data. "
                "Register to save permanently."
            )
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load history: {str(e)}"
        )

@router.post(
    "/migrate-to-user/{user_id}",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Session successfully migrated"},
        404: {"description": "User not found"},
        500: {"description": "Migration failed"}
    }
)
async def migrate_session_to_user_account(
    request: Request,
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Migrate anonymous session history to a registered user.
    
    Args:
        user_id: ID of the user to migrate history to
        request: FastAPI request object
        db: Database session
        
    Returns:
        dict: Migration status and count
        
    Raises:
        HTTPException: If migration fails
    """
    session_token = get_session_token(request)
    
    try:
        migrated_count = await migrate_session_to_user(
            db,
            session_token,
            user_id
        )
        
        return {
            "message": f"Successfully migrated {migrated_count} history items to your account",
            "migrated_count": migrated_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )