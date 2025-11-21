import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://nexus_user:nexus_pass@localhost/nexus")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Find content_view_history records with blank or null content_slug
    blank_slug = conn.execute(text("""
        SELECT id, content_id, content_slug, view_type, viewed_at
        FROM content_view_history
        WHERE content_slug IS NULL OR content_slug = ''
        LIMIT 20;
    """)).fetchall()
    print("History records with blank or null content_slug:")
    for row in blank_slug:
        print(dict(row))

    # Find content_items with blank or null title
    blank_title = conn.execute(text("""
        SELECT id, slug, title FROM content_items WHERE title IS NULL OR title = '' LIMIT 20;
    """)).fetchall()
    print("\nContent items with blank or null title:")
    for row in blank_title:
        print(dict(row))
