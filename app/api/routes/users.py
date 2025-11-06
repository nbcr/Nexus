from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_users():
    """Get users endpoint - to be implemented"""
    return {"message": "Users endpoint - to be implemented"}

@router.post("/")
async def create_user():
    """Create user endpoint - to be implemented"""
    return {"message": "Create user endpoint - to be implemented"}
