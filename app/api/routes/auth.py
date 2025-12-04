from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db import AsyncSessionLocal
from app.schemas import Token, UserCreate, UserResponse, UserLogin
from app.services.user_service import create_user, authenticate_user
from app.services.email_service import email_service
from app.core.auth import create_access_token, verify_token
from app.models import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    from app.services.user_service import get_user_by_username

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


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    import logging

    logger = logging.getLogger("uvicorn.error")
    from app.services.user_service import get_user_by_username, get_user_by_email

    try:
        # Check if username exists
        db_user = await get_user_by_username(db, username=user_data.username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        # Check if email exists
        db_user = await get_user_by_email(db, email=user_data.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Pass password as string directly to user_service
        logger.warning(f"Password length (characters): {len(user_data.password)}")
        user = await create_user(db, user_data)
        # Migrate anonymous session data if visitor_id cookie is present
        from fastapi import Request

        request = Request(scope={})
        visitor_id = request.cookies.get("visitor_id")
        if visitor_id:
            from app.services.session_service import migrate_session_to_user

            await migrate_session_to_user(db, visitor_id, user.id)
        # Send registration email asynchronously
        try:
            await email_service.send_registration_email_async(
                to_email=user_data.email, username=user_data.username
            )
        except Exception as e:
            logger.exception("Email send failed: %s", e)
        return user
    except Exception as e:
        logger.exception("Registration failed: %s", e)
        raise


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    # Migrate anonymous session data if visitor_id cookie is present
    from fastapi import Request

    request = Request(scope={})
    visitor_id = request.cookies.get("visitor_id")
    if visitor_id:
        from app.services.session_service import migrate_session_to_user

        await migrate_session_to_user(db, visitor_id, user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


# Logout endpoint: clears access/refresh tokens
from fastapi import Response


@router.post("/logout")
async def logout(response: Response):
    # Remove access and refresh tokens from cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"detail": "Logged out"}

