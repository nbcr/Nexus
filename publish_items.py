import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:***REMOVED***@localhost:5432/nexus")

conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Publish all items
cursor.execute('UPDATE content_items SET is_published = true WHERE is_published = false')
conn.commit()

# Check result
cursor.execute('SELECT COUNT(*) FROM content_items WHERE is_published = true')
published = cursor.fetchone()[0]
print(f'✅ Published {published} items')

cursor.close()
conn.close()
