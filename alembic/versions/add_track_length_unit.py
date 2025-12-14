"""Add track_length_unit to races table

Revision ID: add_track_unit_003
Revises: add_indexes_002
Create Date: 2025-12-14

This migration:
1. Renames track_length_meters to track_length
2. Adds track_length_unit column with default 'meters'
3. Adds check constraint for valid units
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_track_unit_003'
down_revision = 'add_indexes_002'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Rename track_length_meters to track_length
    op.alter_column('races', 'track_length_meters', new_column_name='track_length')

    # Step 2: Add track_length_unit column with default 'meters'
    op.add_column('races', sa.Column('track_length_unit', sa.String(length=10), nullable=False, server_default='meters'))

    # Step 3: Add check constraint for track_length_unit
    op.create_check_constraint(
        'check_track_length_unit',
        'races',
        "track_length_unit IN ('meters', 'feet')"
    )


def downgrade():
    # Step 1: Drop check constraint
    op.drop_constraint('check_track_length_unit', 'races', type_='check')

    # Step 2: Drop track_length_unit column
    op.drop_column('races', 'track_length_unit')

    # Step 3: Rename track_length back to track_length_meters
    op.alter_column('races', 'track_length', new_column_name='track_length_meters')
