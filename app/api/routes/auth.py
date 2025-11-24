from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db import AsyncSessionLocal
from app.schemas import Token, UserCreate, UserResponse, UserLogin
from app.services.user_service import create_user, authenticate_user
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
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


from app.services.email_service import send_registration_email

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    import logging
    logger = logging.getLogger("uvicorn.error")
    from app.services.user_service import get_user_by_username, get_user_by_email
    try:
        # Check if username exists
        db_user = await get_user_by_username(db, username=user_data.username)
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )

        # Check if email exists
        db_user = await get_user_by_email(db, email=user_data.email)
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Pass password as string directly to user_service
        logger.warning(f"Password length (characters): {len(user_data.password)}")
        user = await create_user(db, user_data)
        # Send registration email
        try:
            send_registration_email(to_email=user_data.email, username=user_data.username)
        except Exception as e:
            logger.exception("Email send failed: %s", e)
        return user
    except Exception as e:
        logger.exception("Registration failed: %s", e)
        raise

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
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
