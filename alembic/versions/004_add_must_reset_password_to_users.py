"""
Add must_reset_password column to users table
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = 'merge_heads_20251124a'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('must_reset_password', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))

def downgrade():
    op.drop_column('users', 'must_reset_password')
