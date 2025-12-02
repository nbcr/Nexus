"""
Script to flag all users for password reset by setting must_reset_password=True.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import update


async def flag_password_reset():
    async with AsyncSessionLocal() as session:
        await session.execute(update(User).values(must_reset_password=True))
        await session.commit()
    print("✅ All users flagged for password reset.")


if __name__ == "__main__":
    asyncio.run(flag_password_reset())
