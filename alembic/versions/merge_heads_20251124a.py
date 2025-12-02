"""
Merge multiple Alembic heads into one
"""

from alembic import op
import sqlalchemy as sa

revision = "merge_heads_20251124a"
down_revision = (
    "003",
    "add_bio_to_uip",
    "add_is_admin_to_users",
    "add_bio_to_uip_short",
)
branch_labels = None
depends_on = None


def upgrade():
    pass
