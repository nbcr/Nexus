"""
Common API Dependencies

This module contains shared dependencies used across API routes, including:
- Database session management
- User authentication
- Permission checking
"""
from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Request, Response # pyright: ignore[reportMissingImports]
from fastapi.security import OAuth2PasswordBearer # pyright: ignore[reportMissingImports]
from sqlalchemy.ext.asyncio import AsyncSession # pyright: ignore[reportMissingImports]
from sqlalchemy import select # pyright: ignore[reportMissingImports]
import uuid

from app.database import AsyncSessionLocal
from app.models import User
from app.models.user import UserSession
from app.core.auth import verify_token
from app.services.user_service import get_user_by_username

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session management.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        ```python
        @router.get("/items")
        async def get_items(db: Annotated[AsyncSession, Depends(get_db)]):
            ...
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If credentials are invalid
        
    Example:
        ```python
        @router.get("/me")
        async def read_me(user: Annotated[User, Depends(get_current_user)]):
            return user
        ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(token)
    if username is None:
        raise credentials_exception
        
    user = await get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get the current active user.
    
    Extends get_current_user to also verify the user is active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# Common dependency types
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_or_create_session(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserSession:
    """
    Dependency to get or create a session for the current user.
    Works for both authenticated and anonymous users.
    
    For anonymous users, creates a session token stored in cookies.
    For authenticated users, uses existing session or creates one.
    
    Args:
        request: FastAPI request object (to read cookies)
        response: FastAPI response object (to set cookies)
        db: Database session
        
    Returns:
        UserSession: Current session (with or without user_id)
    """
    from datetime import datetime, timedelta
    
    # Try to get session token from cookie
    session_token = request.cookies.get("nexus_session")
    
    # Try to find existing session in database
    if session_token:
        result = await db.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
        session = result.scalar_one_or_none()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            await db.commit()
            return session
    
    # Create new session for anonymous user
    session_token = str(uuid.uuid4())
    new_session = UserSession(
        session_token=session_token,
        user_id=None,  # Anonymous
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year for anonymous
        last_activity=datetime.utcnow()
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    # Set cookie for future requests (1 year expiry)
    response.set_cookie(
        key="nexus_session",
        value=session_token,
        max_age=31536000,  # 1 year in seconds
        httponly=True,
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    return new_session


# Alias for backward compatibility
async def get_current_session(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserSession:
    """Alias for get_or_create_session"""
    return await get_or_create_session(request, response, db)