from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from app.core.input_validation import InputValidator
from app.core.secure_request_handler import SecureRequestHandler

from app.db import AsyncSessionLocal
from app.api.v1.deps import get_db
from app.services.session_service import (
    create_anonymous_session,
    track_content_interaction,
    get_session_history,
    migrate_session_to_user,
)

# Single router instance for all session routes
router = APIRouter()


class InterestEvent(BaseModel):
    content_id: int
    interest_score: Optional[int] = None
    hover_duration_ms: Optional[int] = None
    movement_detected: Optional[bool] = None
    slowdowns_detected: Optional[int] = None
    clicks_detected: Optional[int] = None
    was_afk: Optional[bool] = None
    trigger: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/track-interest")
async def track_content_interest(
    interest: InterestEvent,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Track when a user shows interest in content (e.g., hover/click)"""
    import logging

    session_token = get_session_token(request)
    visitor_id = request.cookies.get("visitor_id")
    
    # Validate visitor_id before using it
    if visitor_id:
        visitor_id = InputValidator.validate_visitor_id(visitor_id)

    # Persist the session token for subsequent requests
    if not request.cookies.get("nexus_session"):
        response.set_cookie(
            "nexus_session",
            session_token,
            max_age=60 * 60 * 24 * 30,
            httponly=False,
            samesite="lax",
        )

    logging.debug(
        f"[track-interest] visitor_id={visitor_id}, session_token={session_token}, content_id={interest.content_id}"
    )

    try:
        await track_content_interaction(
            db,
            session_token,
            interest.content_id,
            interaction_type="interest",
            metadata=interest.model_dump(exclude_none=True),
        )
        return {
            "status": "tracked",
            "session_token": session_token,
            "visitor_id": visitor_id,
            "content_id": interest.content_id,
        }
    except Exception as e:
        logging.error(f"[track-interest] Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Tracking interest failed: {str(e)}"
        )


# Note: get_db imported from app.db is reused across routes


def get_session_token(request: Request):
    """Get or create session token from cookies or headers"""
    # Try to get from cookies first
    session_token = request.cookies.get("nexus_session")

    # If not in cookies, check Authorization header for session token
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Session "):
            session_token = auth_header.replace("Session ", "")

    # If still no token, create one (frontend will need to store it)
    if not session_token:
        import uuid
        session_token = str(uuid.uuid4())
    
    # Always validate the session token before use
    session_token = InputValidator.validate_session_token(session_token)

    return session_token


@router.post("/track-view/{content_id}")
async def track_content_view(
    content_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    # Validate content_id
    content_id = InputValidator.validate_integer(content_id, min_val=1, max_val=999999999)
    """Track when a user views content"""
    session_token = get_session_token(request)

    # Ensure the session token is persisted for subsequent calls
    if not request.cookies.get("nexus_session"):
        response.set_cookie(
            "nexus_session",
            session_token,
            max_age=60 * 60 * 24 * 30,
            httponly=False,
            samesite="lax",
        )

    try:
        await track_content_interaction(
            db, session_token, content_id, interaction_type="view"
        )

        return {"status": "tracked", "session_token": session_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tracking failed: {str(e)}")


@router.get("/history")
async def get_user_history(request: Request, db: AsyncSession = Depends(get_db)):
    """Get viewing history for current session"""
    session_token = get_session_token(request)

    try:
        history = await get_session_history(db, session_token)

        return {
            "history": history,
            "session_token": session_token,
            "is_anonymous": True,
            "warning": "Your history is stored with a session cookie. Clear your cookies and you'll lose this data. Register to save permanently.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")


@router.post("/migrate-to-user/{user_id}")
async def migrate_session_to_user_account(
    user_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    """Migrate anonymous session history to a registered user"""
    session_token = get_session_token(request)

    try:
        migrated_count = await migrate_session_to_user(db, session_token, user_id)

        return {
            "message": f"Successfully migrated {migrated_count} history items to your account",
            "migrated_count": migrated_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.get("/session-info")
async def get_session_info(request: Request, db: AsyncSession = Depends(get_db)):
    """Get information about current session"""
    session_token = get_session_token(request)

    try:
        session = await create_anonymous_session(db, session_token)
        history = await get_session_history(db, session_token)

        return {
            "session_token": session_token,
            "session_created": session.created_at,
            "history_count": len(history),
            "is_anonymous": True,
            "warning": "Anonymous session - data may be lost if cookies are cleared",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get session info: {str(e)}"
        )
