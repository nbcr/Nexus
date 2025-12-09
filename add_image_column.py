#!/usr/bin/env python3
"""Add local_image_path column directly using sync psycopg2."""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Parse DATABASE_URL to extract components
db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:***REMOVED***@localhost:5432/nexus"
)

# Remove protocol prefix
db_url = db_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")

# Parse user:password@host:port/dbname
if "@" in db_url:
    auth, host_db = db_url.split("@")
    user, password = auth.split(":")
else:
    user = "postgres"
    password = "***REMOVED***"
    host_db = db_url

if "/" in host_db:
    host_port, dbname = host_db.split("/")
else:
    host_port = host_db
    dbname = "nexus"

if ":" in host_port:
    host, port = host_port.split(":")
    port = int(port)
else:
    host = host_port
    port = 5432

print(f"Connecting to {host}:{port}/{dbname} as {user}...")

try:
    # Connect with psycopg2 (sync)
    conn = psycopg2.connect(
        host=host, port=port, database=dbname, user=user, password=password
    )

    cursor = conn.cursor()

    # Add column if it doesn't exist
    cursor.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS local_image_path VARCHAR(255);
    """
    )

    conn.commit()
    cursor.close()
    conn.close()

    print("✓ Migration applied successfully!")

except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)
