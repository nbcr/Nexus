"""
Session Router

This module handles user session management and content interaction tracking:
- Anonymous session creation and management
- Content view tracking
- Session history retrieval
- Session migration to registered users
"""
from fastapi import APIRouter, HTTPException, Request, Response, Path, Cookie, Depends
from typing import Optional, Dict, List, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user
from app.models import User
from app.services.session_service import (
    create_anonymous_session,
    track_content_interaction,
    get_session_history,
    migrate_session_to_user
)
from app.schemas import ContentWithTopic, SessionResponse, HistoryResponse

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
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Track when a user views content.
    
    Sets a session cookie if one doesn't exist.
    
    Args:
        content_id: ID of the content being viewed
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
            interaction_type="view"
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