#!/usr/bin/env python3
"""
Quick script to make 'yot' user an admin without starting the server
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url_sync = os.getenv("DATABASE_URL_SYNC")
if not database_url_sync:
    raise ValueError("DATABASE_URL_SYNC not found in .env file")

try:
    # Create engine
    engine = create_engine(database_url_sync, echo=False, pool_pre_ping=True)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Find yot user
    yot = session.query(User).filter(User.username == "yot").first()

    if not yot:
        print("❌ User 'yot' not found. Creating user first...")
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
        hashed_pw = pwd_context.hash("password123")

        yot = User(
            username="yot",
            email="yot@nexus.local",
            hashed_password=hashed_pw,
            is_admin=True,
            is_active=True,
        )
        session.add(yot)
        session.commit()
        print("✅ Created user 'yot' with admin=True")
    else:
        # Update existing user to admin
        session.query(User).filter(User.id == yot.id).update({"is_admin": True})
        session.commit()
        print(f"✅ Updated user 'yot' to admin=True (id={yot.id})")

    session.close()
    engine.dispose()

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying alternate connection method...")
    sys.exit(1)
