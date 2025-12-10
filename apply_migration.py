#!/usr/bin/env python
"""Apply migrations to the database."""
import os
import sys
from alembic.config import Config
from alembic import command

# Set database URL
database_url = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/nexus"
)
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
