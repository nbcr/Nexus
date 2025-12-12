"""Add image_data column to content_items for storing WebP images

Revision ID: add_image_data
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
    # Add image_data column for storing WebP images as binary
    # Using LargeBinary which maps to BYTEA in PostgreSQL, LONGBLOB in MySQL
    op.add_column(
        "content_items", sa.Column("image_data", sa.LargeBinary(), nullable=True)
    )


def downgrade() -> None:
    # Remove image_data column
    op.drop_column("content_items", "image_data")
