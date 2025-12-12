import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Parse DATABASE_URL
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL not found in environment variables")

conn = None
cursor = None

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Add column if it doesn't exist
    cursor.execute(
        """
        ALTER TABLE content_items
        ADD COLUMN IF NOT EXISTS local_image_path VARCHAR(255);
    """
    )

    conn.commit()
    print("✓ Column added successfully")

except Exception as e:
    print(f"Error: {e}")
finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
