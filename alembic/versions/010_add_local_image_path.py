"""Add local_image_path column to content_items.

Revision ID: 010
Revises: 009, add_is_admin_to_users
Create Date: 2025-12-09
"""

from alembic import op
import sqlalchemy as sa


revision = "010"
down_revision = ("009", "add_is_admin_to_users")
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "content_items",
        sa.Column("local_image_path", sa.String(255), nullable=True),
    )


def downgrade():
    op.drop_column("content_items", "local_image_path")
