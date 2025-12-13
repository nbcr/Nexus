#!/usr/bin/env python3
import asyncio
from app.database import engine
import sqlalchemy as sa

async def check_columns():
    async with engine.begin() as conn:
        result = await conn.execute(sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'content_items' 
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in result.fetchall()]
        print("content_items columns:")
        for col in columns:
            print(f"  - {col}")
        print(f"\nTotal: {len(columns)} columns")
        print(f"\nimage_data present: {'image_data' in columns}")

asyncio.run(check_columns())

