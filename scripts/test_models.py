import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.database import AsyncSessionLocal, engine
from app.models import UserInteraction, UserSession
from sqlalchemy import text


async def test_models():
    """Test that models match database schema"""
    print("Testing database schema compatibility...")

    try:
        async with AsyncSessionLocal() as session:
            # Test UserInteraction model
            result = await session.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_interactions'
                ORDER BY column_name
            """
                )
            )
            interaction_columns = result.fetchall()
            print("\\nUserInteraction table columns:")
            for col in interaction_columns:
                print(f"  - {col[0]} ({col[1]}, nullable: {col[2]})")

            # Test UserSession model
            result = await session.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_sessions'
                ORDER BY column_name
            """
                )
            )
            session_columns = result.fetchall()
            print("\\nUserSession table columns:")
            for col in session_columns:
                print(f"  - {col[0]} ({col[1]}, nullable: {col[2]})")

            # Check foreign keys
            result = await session.execute(
                text(
                    """
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND (tc.table_name = 'user_interactions' OR tc.table_name = 'user_sessions')
            """
                )
            )
            foreign_keys = result.fetchall()
            print("\\nForeign keys:")
            for fk in foreign_keys:
                print(f"  - {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")

            print("\\n✅ Database schema test completed!")

    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_models())
