#!/usr/bin/env python3
"""
Simple SQL migration script
Run with: python simple_migrate.py
"""
import os
import sys


def run_sql_migration():
    """Run SQL migration using psql command"""

    # Check if we can use psql
    print("Running database migration using SQL file...")
    print("Please run the following command:")
    print()
    print("psql -U your_username -d nexus -f add_content_fields.sql")
    print()
    print("Or if you prefer, run these SQL commands manually:")
    print()

    with open("add_content_fields.sql", "r") as f:
        sql_content = f.read()
        print(sql_content)

    print()
    print("=" * 60)
    print("ALTERNATIVE: Set DATABASE_URL and run migrate_db.py")
    print("=" * 60)
    print()
    print(
        "export DATABASE_URL='postgresql+asyncpg://username:password@localhost:5432/nexus'"
    )
    print("python migrate_db.py")


if __name__ == "__main__":
    run_sql_migration()
