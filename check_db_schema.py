import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print(f"Database URL: {db_url}")

# Test which database we're using
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        print(f"Connected to database: {db_name}")
        
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            LIMIT 10
        """))
        tables = result.fetchall()
        print(f"\nTables in {db_name}:")
        for table in tables:
            print(f"  - {table[0]}")

asyncio.run(check_db())
