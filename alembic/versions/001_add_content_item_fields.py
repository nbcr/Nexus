"""add content item fields

Revision ID: 001
Revises:
Create Date: 2025-11-15

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to content_items table
    op.add_column(
        "content_items", sa.Column("title", sa.String(length=500), nullable=True)
    )
    op.add_column("content_items", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "content_items", sa.Column("category", sa.String(length=100), nullable=True)
    )
    op.add_column(
        "content_items",
        sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )

    # Set default values for existing rows
    op.execute("UPDATE content_items SET title = 'Untitled' WHERE title IS NULL")
    op.execute("UPDATE content_items SET tags = '[]' WHERE tags IS NULL")

    # Make title NOT NULL after setting defaults
    op.alter_column("content_items", "title", nullable=False)


def downgrade():
    # Remove added columns
    op.drop_column("content_items", "tags")
    op.drop_column("content_items", "category")
    op.drop_column("content_items", "description")
    op.drop_column("content_items", "title")
