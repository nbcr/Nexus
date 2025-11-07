"""
Authentication Router

This module handles user authentication and authorization endpoints including:
- User registration
- User login (token generation)
- Current user information

Authentication is handled via OAuth2 with Bearer tokens.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.database import AsyncSessionLocal
from app.schemas import Token, UserCreate, UserResponse, UserLogin
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email
)
from app.core.auth import create_access_token, verify_token
from app.models import User

# Router Configuration
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Dependencies
async def get_db() -> AsyncSession:
    """Dependency for database session management."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
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
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Username or email already exists"}
    }
)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Register a new user.
    
    Args:
        user_data: User registration data including username, email, and password
        db: Database session dependency
        
    Returns:
        The created user object
        
    Raises:
        HTTPException: If username or email is already registered
    """
    # Check if username exists
    if await get_user_by_username(db, username=user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if await get_user_by_email(db, email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await create_user(db, user_data)
    return user

@router.post(
    "/login",
    response_model=Token,
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Invalid credentials"}
    }
)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Authenticate a user and return an access token.
    
    Args:
        response: FastAPI response object for setting cookies
        form_data: OAuth2 form containing username and password
        db: Database session dependency
        
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
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Set the token in an HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="lax",  # CSRF protection
        max_age=1800  # 30 minutes in seconds
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        200: {"description": "Current user details"},
        401: {"description": "Not authenticated"}
    }
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get the current authenticated user's details.
    
    Args:
        current_user: The current user (injected by dependency)
        
    Returns:
        The current user object
    """
    return current_user