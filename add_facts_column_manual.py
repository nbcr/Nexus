#!/usr/bin/env python3
"""Manually add facts column to content_items table"""
import asyncio
from sqlalchemy import text
from app.db import engine


async def add_facts_column():
    """Add facts column if it doesn't exist"""
    async with engine.begin() as conn:
        await conn.execute(
            text("ALTER TABLE content_items ADD COLUMN IF NOT EXISTS facts TEXT")
        )
        print("✓ Facts column added successfully")


if __name__ == "__main__":
    asyncio.run(add_facts_column())
