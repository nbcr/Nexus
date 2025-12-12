import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Use database URL from .env
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        # Check current version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current = result.fetchone()
        if current:
            print(f"Current version in DB: {current[0]}")

            # Update to new version 011
            if current[0] != "011":
                conn.execute(
                    text(
                        "UPDATE alembic_version SET version_num = '011' WHERE version_num = :old_ver"
                    ),
                    {"old_ver": current[0]},
                )
                conn.commit()
                print(f"Updated version from {current[0]} to 011")
            else:
                print("Version is already 011")
        else:
            print("No version found")
except Exception as e:
    print(f"Error: {e}")
