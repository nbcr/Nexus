"""
Add missing columns to user_interest_profiles table
"""

from alembic import op
import sqlalchemy as sa

revision = "add_bio_to_uip"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # Add columns only if they do not exist
    op.execute(
        """
        ALTER TABLE user_interest_profiles ADD COLUMN IF NOT EXISTS bio VARCHAR(500);
        ALTER TABLE user_interest_profiles ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);
        ALTER TABLE user_interest_profiles ADD COLUMN IF NOT EXISTS social_links JSON;
        ALTER TABLE user_interest_profiles ADD COLUMN IF NOT EXISTS expertise JSON;
    """
    )


def downgrade():
    op.drop_column("user_interest_profiles", "bio")
    op.drop_column("user_interest_profiles", "avatar_url")
    op.drop_column("user_interest_profiles", "social_links")
    op.drop_column("user_interest_profiles", "expertise")
