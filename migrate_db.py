#!/usr/bin/env python3
"""
Direct database migration using SQLAlchemy
"""
import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def run_migration():
    """Add new columns to content_items table"""
    async with AsyncSessionLocal() as session:
        try:
            # ...existing code...

            # Add new columns
            await session.execute(
                text(
                    """
                ALTER TABLE content_items 
                ADD COLUMN IF NOT EXISTS title VARCHAR(500);
            """
                )
            )

            await session.execute(
                text(
                    """
                ALTER TABLE content_items 
                ADD COLUMN IF NOT EXISTS description TEXT;
            """
                )
            )

            await session.execute(
                text(
                    """
                ALTER TABLE content_items 
                ADD COLUMN IF NOT EXISTS category VARCHAR(100);
            """
                )
            )

            await session.execute(
                text(
                    """
                ALTER TABLE content_items 
                ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]';
            """
                )
            )

            # Set default values for existing rows
            await session.execute(
                text(
                    """
                UPDATE content_items 
                SET title = 'Untitled' 
                WHERE title IS NULL;
            """
                )
            )

            await session.execute(
                text(
                    """
                UPDATE content_items 
                SET tags = '[]' 
                WHERE tags IS NULL;
            """
                )
            )

            await session.commit()

            # ...existing code...
            # ...existing code...

        except Exception as e:
            await session.rollback()
            # ...existing code...
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_migration())
