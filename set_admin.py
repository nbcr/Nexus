#!/usr/bin/env python3
"""
Set a user as admin directly via database using asyncpg
"""
import asyncio
import sys
import os


async def set_admin():
    import asyncpg

    # Connection parameters (matching app/db.py)
    conn_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", None),
        "database": "nexus",
    }

    # Filter out None password
    if conn_params["password"] is None:
        del conn_params["password"]

    try:
        conn = await asyncpg.connect(**conn_params)

        # Check if yot exists
        user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", "yot")

        if user:
            # Update existing user
            await conn.execute(
                "UPDATE users SET is_admin = true WHERE username = $1", "yot"
            )
            print("✅ User 'yot' is now an admin")
        else:
            print("❌ User 'yot' not found")

        await conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(set_admin())
