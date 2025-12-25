"""create device_tokens table

Revision ID: add_device_tokens
Revises:
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic
revision = 'add_device_tokens'
down_revision = None  # Set this to your latest migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create device_tokens table
    op.create_table(
        'device_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_token', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create indexes
    op.create_index('ix_device_tokens_device_token', 'device_tokens', ['device_token'], unique=True)
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'])
    op.create_index('ix_device_tokens_created_at', 'device_tokens', ['created_at'])
    op.create_index('ix_device_tokens_user_platform', 'device_tokens', ['user_id', 'platform'])

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_device_tokens_user_id',
        'device_tokens', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key
    op.drop_constraint('fk_device_tokens_user_id', 'device_tokens', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_device_tokens_user_platform', 'device_tokens')
    op.drop_index('ix_device_tokens_created_at', 'device_tokens')
    op.drop_index('ix_device_tokens_user_id', 'device_tokens')
    op.drop_index('ix_device_tokens_device_token', 'device_tokens')

    # Drop table
    op.drop_table('device_tokens')
