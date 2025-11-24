"""
Add missing columns to user_interest_profiles table
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_bio_to_user_interest_profiles'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('user_interest_profiles', sa.Column('bio', sa.String(length=500), nullable=True))
    op.add_column('user_interest_profiles', sa.Column('avatar_url', sa.String(length=255), nullable=True))
    op.add_column('user_interest_profiles', sa.Column('social_links', sa.JSON(), nullable=True))
    op.add_column('user_interest_profiles', sa.Column('expertise', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('user_interest_profiles', 'bio')
    op.drop_column('user_interest_profiles', 'avatar_url')
    op.drop_column('user_interest_profiles', 'social_links')
    op.drop_column('user_interest_profiles', 'expertise')
    op.drop_column('user_interest_profiles', 'last_updated')
