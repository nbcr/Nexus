import os
from sqlalchemy import create_engine, text

# Use sync URL from .env
db_url = "postgresql://postgres:***REMOVED***@localhost:5432/nexus"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        # Check current version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current = result.fetchone()
        if current:
            print(f"Current version in DB: {current[0]}")

            # Update if it's '011', revert to 'add_image_data'
            if current[0] == "011":
                conn.execute(
                    text(
                        "UPDATE alembic_version SET version_num = 'add_image_data' WHERE version_num = '011'"
                    )
                )
                conn.commit()
                print("Updated version to add_image_data")
            else:
                print(f"Version is already {current[0]}")
        else:
            print("No version found")
except Exception as e:
    print(f"Error: {e}")
