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
    # Drop the unique constraints first
    op.drop_constraint("topics_title_key", "topics", type_="unique")
    op.drop_constraint("topics_normalized_title_key", "topics", type_="unique")

    # Alter the columns
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

    # Recreate the unique constraints
    op.create_unique_constraint("topics_title_key", "topics", ["title"])
    op.create_unique_constraint(
        "topics_normalized_title_key", "topics", ["normalized_title"]
    )


def downgrade() -> None:
    # Drop the unique constraints
    op.drop_constraint("topics_title_key", "topics", type_="unique")
    op.drop_constraint("topics_normalized_title_key", "topics", type_="unique")

    # Alter the columns back
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

    # Recreate the unique constraints
    op.create_unique_constraint("topics_title_key", "topics", ["title"])
    op.create_unique_constraint(
        "topics_normalized_title_key", "topics", ["normalized_title"]
    )
