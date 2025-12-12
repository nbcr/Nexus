import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL_SYNC")
if not db_url:
    raise ValueError("DATABASE_URL_SYNC not found in .env file")

conn = psycopg2.connect(db_url)
cursor = conn.cursor()

# Check total items
cursor.execute('SELECT COUNT(*) FROM content_items')
total_result = cursor.fetchone()
total = total_result[0] if total_result else 0
print(f'Total content items: {total}')

# Check published items
cursor.execute('SELECT COUNT(*) FROM content_items WHERE is_published = true')
published_result = cursor.fetchone()
published = published_result[0] if published_result else 0
print(f'Published items: {published}')

# Check items with titles
cursor.execute('SELECT id, title, is_published FROM content_items LIMIT 5')
items = cursor.fetchall()
print('\nFirst 5 items:')
for item in items:
    print(f'  ID: {item[0]}, Title: {item[1]}, Published: {item[2]}')

cursor.close()
conn.close()
