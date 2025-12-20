"""add_user_bulls_sell_table

Revision ID: add_user_bulls_001
Revises: 7a6581a8690c
Create Date: 2025-12-18 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_bulls_001'
down_revision = '7a6581a8690c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_bulls_sell table
    op.create_table('user_bulls_sell',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('breed', sa.String(length=100), nullable=True),
        sa.Column('birth_year', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('owner_mobile', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create indexes
    op.create_index(op.f('ix_user_bulls_sell_user_id'), 'user_bulls_sell', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_bulls_sell_status'), 'user_bulls_sell', ['status'], unique=False)
    op.create_index(op.f('ix_user_bulls_sell_created_at'), 'user_bulls_sell', ['created_at'], unique=False)
    op.create_index(op.f('ix_user_bulls_sell_expires_at'), 'user_bulls_sell', ['expires_at'], unique=False)

    # Create composite index for efficient queries
    op.create_index('ix_user_bulls_sell_user_status', 'user_bulls_sell', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_user_bulls_sell_user_status', table_name='user_bulls_sell')
    op.drop_index(op.f('ix_user_bulls_sell_expires_at'), table_name='user_bulls_sell')
    op.drop_index(op.f('ix_user_bulls_sell_created_at'), table_name='user_bulls_sell')
    op.drop_index(op.f('ix_user_bulls_sell_status'), table_name='user_bulls_sell')
    op.drop_index(op.f('ix_user_bulls_sell_user_id'), table_name='user_bulls_sell')

    # Drop table
    op.drop_table('user_bulls_sell')
