"""Merge migration heads 004 and 008

Revision ID: 009
Revises: 004, 008
Create Date: 2025-12-07
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade():
    # Merge heads - no operations needed
    pass


def downgrade():
    # Merge heads - no operations needed
    pass
