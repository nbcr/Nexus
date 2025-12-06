"""Increase title length for topics to accommodate longer titles

Revision ID: 006
Revises: 005
Create Date: 2025-12-06 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter the columns to increase varchar length
    op.alter_column(
        "topics",
        "title",
        existing_type=sa.String(200),
        type_=sa.String(500),
        existing_nullable=False,
    )
    op.alter_column(
        "topics",
        "normalized_title",
        existing_type=sa.String(200),
        type_=sa.String(500),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Alter the columns back to original size
    op.alter_column(
        "topics",
        "title",
        existing_type=sa.String(500),
        type_=sa.String(200),
        existing_nullable=False,
    )
    op.alter_column(
        "topics",
        "normalized_title",
        existing_type=sa.String(500),
        type_=sa.String(200),
        existing_nullable=False,
    )
