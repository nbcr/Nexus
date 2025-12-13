#!/usr/bin/env python3
import asyncio
from app.database import engine
import sqlalchemy as sa


async def add_image_data_column():
    async with engine.begin() as conn:
        try:
            # Check if column exists
            result = await conn.execute(
                sa.text(
                    """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'content_items' AND column_name = 'image_data'
            """
                )
            )

            if result.fetchone():
                print("✓ image_data column already exists")
                return

            print("Adding image_data column...")
            await conn.execute(
                sa.text(
                    """
                ALTER TABLE content_items 
                ADD COLUMN image_data bytea NULL
            """
                )
            )
            print("✓ Successfully added image_data column")

        except Exception as e:
            print(f"✗ Error: {e}")


asyncio.run(add_image_data_column())
