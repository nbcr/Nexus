import asyncio
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.database import engine, Base
from app.models import User, UserSession, Topic, ContentItem, UserInteraction, UserInterestProfile


async def update_database():
    """Update database schema to match models"""
    print("Updating database schema...")
    
    try:
        # This will create any missing tables and update schema
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database schema updated successfully!")
        
        # Test the connection and schema
        async with engine.connect() as conn:
            # Check if user_sessions table exists and has correct columns
            result = await conn.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user_interactions' 
                AND column_name = 'session_id'
            """)
            session_id_exists = result.fetchone()
            
            if session_id_exists:
                print("✅ session_id column exists in user_interactions table")
            else:
                print("❌ session_id column missing from user_interactions table")
                
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(update_database())
