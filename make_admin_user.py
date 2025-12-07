#!/usr/bin/env python
"""
Script to make a user an admin
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.config import settings


def make_admin(username: str):
    """Make a user an admin"""
    # Create database engine
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URL), echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find user by username
        user = db.query(User).filter(User.username == username).first()

        if not user:
            print(f"❌ User '{username}' not found")
            return False

        if user.is_admin:
            print(f"ℹ️ User '{username}' is already an admin")
            return True

        # Set user as admin
        user.is_admin = True
        db.commit()

        print(f"✅ User '{username}' is now an admin")
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin_user.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    success = make_admin(username)
    sys.exit(0 if success else 1)
