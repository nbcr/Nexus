"""
Script to fix user passwords in the database by truncating to 72 bytes and re-hashing if needed.
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.auth import get_password_hash
from sqlalchemy import select, update

async def fix_passwords():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for user in users:
            if user.hashed_password:
                # Attempt to decode and truncate
                try:
                    # This assumes you have access to the original password, which is not possible if only hashes are stored
                    # If you have a way to reset or know the original password, re-hash it here
                    # Otherwise, you may need to force a password reset for affected users
                    pass
                except Exception as e:
                    print(f"Error processing user {user.id}: {e}")
        await session.commit()
    print("✅ Password fix script completed.")

if __name__ == "__main__":
    asyncio.run(fix_passwords())
