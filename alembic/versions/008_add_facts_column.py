"""Add facts column to content_items

Revision ID: 008
Revises: 007
Create Date: 2025-12-07
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("content_items", sa.Column("facts", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("content_items", "facts")
