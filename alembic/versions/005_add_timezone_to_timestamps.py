"""Add timezone to timestamp columns

Revision ID: 005_add_timezone_to_timestamps
Revises: 004_add_must_reset_password_to_users
Create Date: 2025-12-06 12:20:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005_add_timezone_to_timestamps"
down_revision = "004_add_must_reset_password_to_users"
branch_labels = None
depends_on = None


def upgrade():
    # Convert DateTime columns to TIMESTAMP WITH TIME ZONE

    # user_sessions table
    op.execute(
        "ALTER TABLE user_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE user_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITH TIME ZONE USING expires_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE user_sessions ALTER COLUMN last_activity TYPE TIMESTAMP WITH TIME ZONE USING last_activity AT TIME ZONE 'UTC'"
    )

    # user_interactions table
    op.execute(
        "ALTER TABLE user_interactions ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"
    )

    # content_view_history table
    op.execute(
        "ALTER TABLE content_view_history ALTER COLUMN viewed_at TYPE TIMESTAMP WITH TIME ZONE USING viewed_at AT TIME ZONE 'UTC'"
    )

    # users table
    op.execute(
        "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMP WITH TIME ZONE USING last_login AT TIME ZONE 'UTC'"
    )

    # content_items table
    op.execute(
        "ALTER TABLE content_items ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE content_items ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'"
    )

    # topics table
    op.execute(
        "ALTER TABLE topics ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE topics ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'"
    )


def downgrade():
    # Revert to TIMESTAMP WITHOUT TIME ZONE

    # user_sessions table
    op.execute(
        "ALTER TABLE user_sessions ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE user_sessions ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE user_sessions ALTER COLUMN last_activity TYPE TIMESTAMP WITHOUT TIME ZONE"
    )

    # user_interactions table
    op.execute(
        "ALTER TABLE user_interactions ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )

    # content_view_history table
    op.execute(
        "ALTER TABLE content_view_history ALTER COLUMN viewed_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )

    # users table
    op.execute(
        "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMP WITHOUT TIME ZONE"
    )

    # content_items table
    op.execute(
        "ALTER TABLE content_items ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE content_items ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )

    # topics table
    op.execute(
        "ALTER TABLE topics ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE topics ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
