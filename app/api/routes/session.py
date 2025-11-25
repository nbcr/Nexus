from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db import AsyncSessionLocal
from app.services.session_service import (
    create_anonymous_session, 
    track_content_interaction, 
    get_session_history,
    migrate_session_to_user,
    # Add a stub for interest tracking if not present
)
@router.post("/track-interest/{content_id}")
async def track_content_interest(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Track when a user shows interest in content (e.g., hover/click)"""
    session_token = get_session_token(request)
    visitor_id = request.cookies.get("visitor_id")
    # Debug logging for backend troubleshooting
    import logging
    logging.debug(f"[track-interest] visitor_id={visitor_id}, session_token={session_token}, content_id={content_id}")
    try:
        await track_content_interaction(
            db,
            session_token,
            content_id,
            interaction_type="interest"
        )
        return {
            "status": "tracked",
            "session_token": session_token,
            "visitor_id": visitor_id,
            "content_id": content_id
        }
    except Exception as e:
        logging.error(f"[track-interest] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Tracking interest failed: {str(e)}")
from app.schemas import ContentWithTopic

router = APIRouter()

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

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
    
    return session_token

@router.post("/track-view/{content_id}")
async def track_content_view(
    content_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Track when a user views content"""
    session_token = get_session_token(request)
    
    try:
        await track_content_interaction(
            db, 
            session_token, 
            content_id, 
            interaction_type="view"
        )
        
        return {"status": "tracked", "session_token": session_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tracking failed: {str(e)}")

@router.get("/history")
async def get_user_history(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get viewing history for current session"""
    session_token = get_session_token(request)
    
    try:
        history = await get_session_history(db, session_token)
        
        return {
            "history": history,
            "session_token": session_token,
            "is_anonymous": True,
            "warning": "Your history is stored with a session cookie. Clear your cookies and you'll lose this data. Register to save permanently."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")

@router.post("/migrate-to-user/{user_id}")
async def migrate_session_to_user_account(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Migrate anonymous session history to a registered user"""
    session_token = get_session_token(request)
    
    try:
        migrated_count = await migrate_session_to_user(db, session_token, user_id)
        
        return {
            "message": f"Successfully migrated {migrated_count} history items to your account",
            "migrated_count": migrated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/session-info")
async def get_session_info(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
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
            "warning": "Anonymous session - data may be lost if cookies are cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")
