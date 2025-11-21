"""add content view history table

Revision ID: 003
Revises: 002
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create content_view_history table
    op.create_table('content_view_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_token', sa.String(length=255), nullable=True),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('content_slug', sa.String(length=255), nullable=False),
        sa.Column('view_type', sa.String(length=50), nullable=False),  # 'seen', 'clicked', 'read'
        sa.Column('viewed_at', sa.DateTime(), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_view_history_content_id'), 'content_view_history', ['content_id'], unique=False)
    op.create_index(op.f('ix_content_view_history_content_slug'), 'content_view_history', ['content_slug'], unique=False)
    op.create_index(op.f('ix_content_view_history_session_token'), 'content_view_history', ['session_token'], unique=False)
    op.create_index(op.f('ix_content_view_history_user_id'), 'content_view_history', ['user_id'], unique=False)
    
    # Add unique slug column to content_items
    op.add_column('content_items', sa.Column('slug', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_content_items_slug'), 'content_items', ['slug'], unique=True)
    
    # Generate slugs for existing content (based on id for now)
    op.execute("UPDATE content_items SET slug = 'content-' || id WHERE slug IS NULL")
    
    # Make slug NOT NULL after populating
    op.alter_column('content_items', 'slug', nullable=False)


def downgrade():
    # Remove slug from content_items
    op.drop_index(op.f('ix_content_items_slug'), table_name='content_items')
    op.drop_column('content_items', 'slug')
    
    # Drop content_view_history table
    op.drop_index(op.f('ix_content_view_history_user_id'), table_name='content_view_history')
    op.drop_index(op.f('ix_content_view_history_session_token'), table_name='content_view_history')
    op.drop_index(op.f('ix_content_view_history_content_slug'), table_name='content_view_history')
    op.drop_index(op.f('ix_content_view_history_content_id'), table_name='content_view_history')
    op.drop_table('content_view_history')
