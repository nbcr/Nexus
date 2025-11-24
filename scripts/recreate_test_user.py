import asyncio
from app.db import AsyncSessionLocal
from app.models import User
from app.core.auth import get_password_hash

USERNAME = "testuser"
EMAIL = "testuser@example.com"
PASSWORD = "testpass"

async def recreate_test_user():
    async with AsyncSessionLocal() as db:
        # Delete existing user
        user = await db.execute(User.__table__.select().where(User.username == USERNAME))
        user_obj = user.scalar_one_or_none()
        if user_obj:
            await db.delete(user_obj)
            await db.commit()
            print(f"Deleted user: {USERNAME}")
        # Create new user
        hashed_password = get_password_hash(PASSWORD)
        new_user = User(username=USERNAME, email=EMAIL, hashed_password=hashed_password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print(f"Created user: {USERNAME}")

if __name__ == "__main__":
    asyncio.run(recreate_test_user())
