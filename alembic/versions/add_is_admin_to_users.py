"""
Add is_admin column to users table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_admin_to_users'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))

def downgrade():
    pass
