def upgrade():
	pass
"""
Add is_admin column to users table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_admin_to_users'
down_revision = '001'
branch_labels = None
depends_on = None




