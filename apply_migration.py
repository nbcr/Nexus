#!/usr/bin/env python
"""Apply migrations to the database."""
import os
import sys
from alembic.config import Config
from alembic import command

# Set database URL from environment
from dotenv import load_dotenv
load_dotenv()

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL not found in .env file")
os.environ["DATABASE_URL"] = database_url

# Create alembic config
alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", database_url.replace("+asyncpg", ""))

# Run upgrade
try:
    command.upgrade(alembic_cfg, "head")
    print("Migration completed successfully!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
