"""add user debug mode

Revision ID: 002
Revises: 001
Create Date: 2025-11-16

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # Add debug_mode column to users table
    op.add_column("users", sa.Column("debug_mode", sa.Boolean(), nullable=True))

    # Set default value for existing users
    op.execute("UPDATE users SET debug_mode = FALSE WHERE debug_mode IS NULL")

    # Make debug_mode NOT NULL with default FALSE
    op.alter_column(
        "users", "debug_mode", nullable=False, server_default=sa.text("FALSE")
    )


def downgrade():
    # Remove debug_mode column
    op.drop_column("users", "debug_mode")
