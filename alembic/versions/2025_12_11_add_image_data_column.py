"""Add image_data column to content_items for storing WebP images

Revision ID: add_image_data
Revises: 
Create Date: 2025-12-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_image_data'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add image_data column as LONGBLOB (MySQL) / BYTEA (PostgreSQL)
    op.add_column('content_items', 
                  sa.Column('image_data', sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    # Remove image_data column
    op.drop_column('content_items', 'image_data')
