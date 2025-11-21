
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate
from app.services.user_service import create_user, get_user_by_email
from app.services.email_service import send_registration_email
from app.database import get_db

router = APIRouter()

@router.get("/")
async def get_users():
    return {"message": "Users endpoint - to be implemented"}

@router.post("/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing = await get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = await create_user(db, user)
    # Send registration email
    try:
        send_registration_email(to_email=user.email, username=user.username)
    except Exception as e:
        # Log error, but don't block registration
        print(f"Email send failed: {e}")
    return {"message": "User registered successfully", "user_id": db_user.id}
