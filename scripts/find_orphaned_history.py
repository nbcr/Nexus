import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://nexus_user:nexus_pass@localhost/nexus")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    output_lines = []
    # Find history records with content_id not in content_items
    orphaned = conn.execute(text("""
        SELECT h.id, h.content_id, h.content_slug, h.view_type, h.viewed_at
        FROM content_view_history h
        LEFT JOIN content_items c ON h.content_id = c.id
        WHERE c.id IS NULL
        LIMIT 20;
    """)).fetchall()
    output_lines.append("Orphaned history records (content_id not found in content_items):")
    for row in orphaned:
        output_lines.append(str(dict(row)))

    # Find content_items with missing or empty title
    missing_title = conn.execute(text("""
        SELECT id, slug, title FROM content_items WHERE title IS NULL OR title = '' LIMIT 20;
    """)).fetchall()
    output_lines.append("\nContent items with missing/empty title:")
    for row in missing_title:
        output_lines.append(str(dict(row)))

    # Print to screen
    for line in output_lines:
        print(line)

    # Write to file
    with open("orphaned_history_output.txt", "w") as f:
        for line in output_lines:
            f.write(line + "\n")
