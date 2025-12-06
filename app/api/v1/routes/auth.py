from fastapi import APIRouter, Response, Depends, HTTPException, status, Request, Cookie
from typing import Annotated, Optional
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


@router.post("/logout")
async def logout(response: Response):
    """Logout endpoint: clears access/refresh tokens"""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"detail": "Logged out"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Dependencies
async def get_db():
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
    await _migrate_anonymous_session(db, request, nexus_session, user.id)

    email_status, email_error = await _send_registration_email(
        db, user_data.email, user.username
    )

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


async def _migrate_anonymous_session(
    db: AsyncSession, request: Request, nexus_session: Optional[str], user_id: int
) -> None:
    """Migrate anonymous session data to new user account"""
    session_token = nexus_session or request.cookies.get("nexus_session")
    if not session_token:
        return

    try:
        migrated_count = await migrate_session_to_user(db, session_token, user_id)
        if migrated_count > 0:
            print(
                f"Migrated {migrated_count} interactions from anonymous session to user {user_id}"
            )
    except Exception as e:
        print(f"Failed to migrate session data: {str(e)}")


async def _send_registration_email(
    db: AsyncSession, email: str, username: str
) -> tuple[str, Optional[str]]:
    """Send registration email and check for Brevo email issues"""
    from sqlalchemy import select
    from app.models.user import BrevoEmailEvent

    stmt = (
        select(BrevoEmailEvent)
        .where(BrevoEmailEvent.email == email)
        .order_by(BrevoEmailEvent.received_at.desc())
        .limit(1)
    )
    brevo_result = await db.execute(stmt)
    brevo_event = brevo_result.scalars().first()

    if brevo_event:
        return "error", "Email not working. Try a different one."

    try:
        success = await email_service.send_registration_email_async(email, username)
        if not success:
            return "error", "Registration email failed to send."
        return "ok", None
    except Exception as e:
        return "error", str(e)


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
    stmt = (
        select(BrevoEmailEvent)
        .where(BrevoEmailEvent.email == email)
        .order_by(BrevoEmailEvent.received_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    event = result.scalars().first()

    if event:
        return {
            "has_error": True,
            "message": "Email not working. Try a different one.",
            "event_type": event.event_type,
        }

    return {"has_error": False, "message": None, "event_type": None}


# === Password Reset Flow ===
import secrets
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel


class ForgotPasswordRequest(BaseModel):
    username_or_email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Send password reset email to user"""
    username_or_email = request.username_or_email.strip()

    if not username_or_email:
        raise HTTPException(status_code=400, detail="Username or email required")

    # Find user by username or email
    user = await get_user_by_username(db, username_or_email) or await get_user_by_email(
        db, username_or_email
    )

    if not user or not user.email:
        # Return generic message for security (don't reveal if account exists)
        return {"detail": "If account exists, reset link sent to email"}

    # Generate reset token (expires in 1 hour)
    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.utcnow() + timedelta(hours=1)

    # Store reset token in user record
    user.password_reset_token = reset_token
    user.password_reset_expires = reset_expires
    db.add(user)
    await db.commit()

    # Send reset email
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    subject = "Nexus - Reset Your Password"
    html_content = f"""
    <h2>Password Reset Request</h2>
    <p>Click the link below to reset your password. This link expires in 1 hour.</p>
    <a href="{reset_url}" style="background: #0078d7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
        Reset Password
    </a>
    <p>Or copy this link: {reset_url}</p>
    <p>If you didn't request this, you can safely ignore this email.</p>
    """

    try:
        print(f"[FORGOT-PASSWORD] Attempting to send reset email to {user.email}")
        await asyncio.to_thread(
            email_service.send_email,
            to=user.email,
            subject=subject,
            html_content=html_content,
        )
        print(f"[FORGOT-PASSWORD] Email sent successfully to {user.email}")
    except Exception as e:
        print(
            f"[FORGOT-PASSWORD] Failed to send email to {user.email}: {type(e).__name__}: {e}"
        )
        # Still return success message for security

    return {"detail": "If account exists, reset link sent to email"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Reset password using reset token"""
    token = request.token.strip()
    new_password = request.new_password.strip()

    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password required")

    if len(new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )

    # Find user with matching reset token
    from sqlalchemy import select

    stmt = select(User).where(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.utcnow(),
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Update password
    from app.services.user_service import hash_password

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.add(user)
    await db.commit()

    # Send confirmation email
    subject = "Nexus - Password Reset Successful"
    html_content = """
    <h2>Password Changed</h2>
    <p>Your password has been successfully reset.</p>
    <p>You can now log in with your new password.</p>
    <p>If you didn't make this change, please contact support immediately.</p>
    """

    try:
        await asyncio.to_thread(
            email_service.send_email,
            to=user.email,
            subject=subject,
            html_content=html_content,
        )
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")

    return {"detail": "Password reset successfully"}
