#!/usr/bin/env python
"""Apply migrations to the database."""
import os
import sys
from alembic.config import Config
from alembic import command

# Set database URL
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:***REMOVED***@localhost:5432/nexus"

# Create alembic config
alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", "postgresql://postgres:***REMOVED***@localhost:5432/nexus")

# Run upgrade
try:
    command.upgrade(alembic_cfg, "head")
    print("Migration completed successfully!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
