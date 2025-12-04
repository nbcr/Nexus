"""Add brevo_email_events table for tracking email validation issues."""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_brevo_email_events"
down_revision = "merge_heads_20251124a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brevo_email_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_data", sa.String(length=1000), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_brevo_email_events_email"), "brevo_email_events", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_brevo_email_events_email"), table_name="brevo_email_events")
    op.drop_table("brevo_email_events")
