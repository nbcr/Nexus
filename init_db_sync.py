#!/usr/bin/env python3
"""
Synchronous database initialization script
"""
import os
import sys
from sqlalchemy import create_engine

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.db import Base
from app.models import (
    User,
    UserSession,
    Topic,
    ContentItem,
    UserInteraction,
    UserInterestProfile,
)

# Use sync connection string
DATABASE_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:***REMOVED***@localhost:5432/nexus")

def init_database():
    """Initialize database tables using synchronous engine"""
    print("Creating database tables (sync)...")
    
    # Create sync engine
    engine = create_engine(DATABASE_URL, echo=False)
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
