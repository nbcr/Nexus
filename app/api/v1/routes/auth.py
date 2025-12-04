from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/debug")
async def debug_auth_router():
    return {"status": "auth router loaded"}


@router.post("/logout")
async def logout(response: Response):
    """Logout endpoint: clears access/refresh tokens"""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"detail": "Logged out"}


"""
Authentication Router

This module handles user authentication and authorization endpoints including:
- User registration
- User login (token generation)
- Current user information

Authentication is handled via OAuth2 with Bearer tokens.
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db import AsyncSessionLocal
from app.schemas import Token, UserCreate, UserResponse, UserLogin, RegisterResponse
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email,
)
from app.services.session_service import migrate_session_to_user
from app.services.email_service import email_service
from app.core.auth import create_access_token, verify_token
from app.core.config import settings
from app.models import User

# Router Configuration
router = APIRouter()


@router.get("/debug")
async def debug_auth_router():
    return {"status": "auth router loaded"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Dependencies
async def get_db() -> AsyncSession:
    """Dependency for database session management."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# --- Token Refresh Endpoint ---
from datetime import timedelta
from app.schemas import Token


@router.post(
    "/refresh",
    response_model=Token,
    responses={
        200: {"description": "Successfully refreshed token"},
        401: {"description": "Not authenticated"},
    },
)
async def refresh_token(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Optional[str] = Cookie(default=None),
) -> Token:
    """
    Issue a new JWT if the user has a valid session (access_token cookie).
    """
    token = None
    # Try to get token from cookie or Authorization header
    if access_token:
        token = access_token.replace("Bearer ", "")
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token_expires = timedelta(minutes=30)
    new_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=new_token, token_type="bearer")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency to get the current authenticated user."""
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


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Username or email already exists"},
    },
)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    nexus_session: Optional[str] = Cookie(default=None),
) -> User:
    """
    Register a new user and migrate any anonymous session data.

    Args:
        user_data: User registration data including username, email, and password
        request: FastAPI request object for session management
        db: Database session dependency
        nexus_session: Optional session cookie for migration

    Returns:
        The created user object

    Raises:
        HTTPException: If username or email is already registered
    """
    # Check if username exists
    if await get_user_by_username(db, username=user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    if await get_user_by_email(db, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = await create_user(db, user_data)

    # Migrate anonymous session data if session token exists
    session_token = nexus_session or request.cookies.get("nexus_session")
    if session_token:
        try:
            migrated_count = await migrate_session_to_user(db, session_token, user.id)
            if migrated_count > 0:
                print(
                    f"Migrated {migrated_count} interactions from anonymous session to user {user.id}"
                )
        except Exception as e:
            # Log the error but don't fail registration
            print(f"Failed to migrate session data: {str(e)}")

    email_status = "ok"
    email_error: Optional[str] = None
    
    # Check for Brevo email validation issues
    from sqlalchemy import select
    from app.models.user import BrevoEmailEvent
    stmt = select(BrevoEmailEvent).where(
        BrevoEmailEvent.email == user_data.email
    ).order_by(BrevoEmailEvent.received_at.desc()).limit(1)
    brevo_result = await db.execute(stmt)
    brevo_event = brevo_result.scalars().first()
    
    if brevo_event:
        email_status = "error"
        email_error = "Email not working. Try a different one."
    else:
        try:
            success = await email_service.send_registration_email_async(
                user_data.email, user.username
            )
            if not success:
                email_status = "error"
                email_error = "Registration email failed to send."
        except Exception as e:
            email_status = "error"
            email_error = str(e)

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    if email_status != "ok" and not settings.debug:
        # Redact details in production
        email_error = "Email delivery encountered a problem."

    return RegisterResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        email_status=email_status,
        email_error=email_error,
    )


@router.post(
    "/login",
    response_model=Token,
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    response: Response,
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    nexus_session: Optional[str] = Cookie(default=None),
) -> Token:
    """
    Authenticate a user, return an access token, and migrate any anonymous session data.

    Args:
        response: FastAPI response object for setting cookies
        request: FastAPI request object for session management
        form_data: OAuth2 form containing username and password
        db: Database session dependency
        nexus_session: Optional session cookie for migration

    Returns:
        Token object containing the access token

    Raises:
        HTTPException: If credentials are invalid
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Migrate anonymous session data if session token exists
    session_token = nexus_session or request.cookies.get("nexus_session")
    if session_token:
        try:
            migrated_count = await migrate_session_to_user(db, session_token, user.id)
            if migrated_count > 0:
                print(
                    f"Migrated {migrated_count} interactions from anonymous session to user {user.id}"
                )
        except Exception as e:
            # Log the error but don't fail login
            print(f"Failed to migrate session data during login: {str(e)}")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Set the token in an HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="lax",  # CSRF protection
        max_age=1800,  # 30 minutes in seconds
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        200: {"description": "Current user details"},
        401: {"description": "Not authenticated"},
    },
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get the current authenticated user's details.

    Args:
        current_user: The current user (injected by dependency)

    Returns:
        The current user object
    """
    return current_user


@router.get("/check-email-status")
async def check_email_status(email: str, db: AsyncSession = Depends(get_db)):
    """Check if an email has failed Brevo validation."""
    from sqlalchemy import select
    from app.models.user import BrevoEmailEvent
    
    # Check for any failed email events
    stmt = select(BrevoEmailEvent).where(
        BrevoEmailEvent.email == email
    ).order_by(BrevoEmailEvent.received_at.desc()).limit(1)
    
    result = await db.execute(stmt)
    event = result.scalars().first()
    
    if event:
        return {
            "has_error": True,
            "message": "Email not working. Try a different one.",
            "event_type": event.event_type
        }
    
    return {
        "has_error": False,
        "message": None,
        "event_type": None
    }
