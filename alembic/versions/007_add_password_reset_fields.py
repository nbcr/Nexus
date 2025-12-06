"""Add password reset fields to users table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    # Add password reset token column
    op.add_column(
        "users",
        sa.Column(
            "password_reset_token",
            sa.String(255),
            nullable=True,
            unique=True,
        ),
    )
    # Add password reset expiry column
    op.add_column(
        "users",
        sa.Column(
            "password_reset_expires",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # Create index on password reset token for quick lookup
    op.create_index(
        op.f("ix_users_password_reset_token"),
        "users",
        ["password_reset_token"],
        unique=True,
    )


def downgrade():
    # Drop index
    op.drop_index(op.f("ix_users_password_reset_token"), table_name="users")
    # Remove columns
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
