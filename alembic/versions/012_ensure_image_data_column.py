"""Ensure image_data column exists with proper error handling

Revision ID: 012
Revises: 011
Create Date: 2025-12-12

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Ensure image_data column exists in content_items.
    This migration is a safety net in case 011 didn't apply properly.
    """
    # Get the bind context
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check current columns
    columns = {col["name"] for col in inspector.get_columns("content_items")}

    if "image_data" not in columns:
        # Add the column if it doesn't exist
        op.add_column(
            "content_items", sa.Column("image_data", postgresql.BYTEA(), nullable=True)
        )
        print("✓ Added missing image_data column to content_items")
    else:
        print("✓ image_data column already exists")


def downgrade() -> None:
    """Remove image_data column if needed"""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = {col["name"] for col in inspector.get_columns("content_items")}

    if "image_data" in columns:
        op.drop_column("content_items", "image_data")
