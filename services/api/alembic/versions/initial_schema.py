"""initial schema

Revision ID: initial_schema
Revises: 
Create Date: 2024-10-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Check if table exists before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'user_tokens' not in tables:
        # User tokens table
        op.create_table(
            'user_tokens',
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('access_token', sa.String(), nullable=False),
            sa.Column('date_added', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('user_id')
        )
    
    if 'song_mappings' not in tables:
        op.create_table(
            'song_mappings',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('trigger_song_id', sa.String(), nullable=False),
            sa.Column('queue_song_id', sa.String(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['user_tokens.user_id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_song_mappings_user_id', 'song_mappings', ['user_id'])
        op.create_index('idx_song_mappings_trigger_song', 'song_mappings', ['trigger_song_id'])

def downgrade():
    op.drop_index('idx_song_mappings_trigger_song')
    op.drop_index('idx_song_mappings_user_id')
    op.drop_table('song_mappings')
    op.drop_table('user_tokens')