"""Add image_data column to content_items for storing WebP images

Revision ID: 011
Revises: 010
Create Date: 2025-12-11

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column already exists before adding
    # This prevents errors if migration is run multiple times
    try:
        inspector = sa.inspect(op.get_context().bind)
        if inspector is not None:
            columns = [col["name"] for col in inspector.get_columns("content_items")]
            if "image_data" in columns:
                return  # Column already exists, skip
    except Exception:
        pass  # Proceed with adding column if inspection fails

    # Add image_data column for storing WebP images as binary
    # Use BYTEA explicitly for PostgreSQL compatibility
    op.add_column(
        "content_items",
        sa.Column("image_data", postgresql.BYTEA(), nullable=True, server_default=None),
    )


def downgrade() -> None:
    # Check if column exists before removing
    try:
        inspector = sa.inspect(op.get_context().bind)
        if inspector is not None:
            columns = [col["name"] for col in inspector.get_columns("content_items")]
            if "image_data" not in columns:
                return  # Column doesn't exist, skip
    except Exception:
        return  # Proceed without downgrade if inspection fails

    op.drop_column("content_items", "image_data")
