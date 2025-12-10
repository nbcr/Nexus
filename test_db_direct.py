#!/usr/bin/env python
import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    from app.db import engine, AsyncSessionLocal
    from sqlalchemy import select, text
    
    print("Testing database connection...")
    try:
        # Test raw connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✓ Raw connection successful")
        
        # Test session
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) as count FROM content_item"))
            count = result.scalar()
            print(f"✓ Session connection successful, {count} items in DB")
        
        print("SUCCESS: Database is accessible")
        sys.exit(0)
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

asyncio.run(test_connection())
