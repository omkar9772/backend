"""Add race_days table and restructure races

Revision ID: add_race_days_001
Revises: f21b2c2270f5
Create Date: 2025-12-14

This migration:
1. Creates the race_days table
2. Migrates existing race data to the new two-tier structure
3. Updates race_results to reference race_days instead of races
4. Modifies races table structure

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_race_days_001'
down_revision = 'f21b2c2270f5'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Create race_days table
    op.create_table('race_days',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('race_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('race_date', sa.Date(), nullable=False),
        sa.Column('day_subtitle', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('total_participants', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('scheduled', 'in_progress', 'completed', 'cancelled')", name='check_race_day_status'),
        sa.CheckConstraint('day_number > 0', name='check_day_number_positive'),
        sa.ForeignKeyConstraint(['race_id'], ['races.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Step 2: Add new columns to races table (start_date, end_date)
    op.add_column('races', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('races', sa.Column('end_date', sa.Date(), nullable=True))

    # Step 3: Migrate existing race data
    # For each existing race, copy race_date to both start_date and end_date
    # and create a corresponding race_day entry
    op.execute("""
        UPDATE races
        SET start_date = race_date, end_date = race_date
        WHERE start_date IS NULL AND end_date IS NULL
    """)

    # Create race_day entries for all existing races
    op.execute("""
        INSERT INTO race_days (id, race_id, day_number, race_date, status, total_participants, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            id as race_id,
            1 as day_number,
            race_date,
            status,
            total_participants,
            NOW(),
            NOW()
        FROM races
    """)

    # Step 4: Add race_day_id column to race_results
    op.add_column('race_results', sa.Column('race_day_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Step 5: Migrate race_results to reference race_days
    # Link each result to the race_day that was created for its race
    op.execute("""
        UPDATE race_results
        SET race_day_id = race_days.id
        FROM race_days
        WHERE race_results.race_id = race_days.race_id
    """)

    # Step 6: Make race_day_id non-nullable after data migration
    op.alter_column('race_results', 'race_day_id', nullable=False)

    # Step 7: Add foreign key constraint for race_day_id
    op.create_foreign_key(
        'race_results_race_day_id_fkey',
        'race_results', 'race_days',
        ['race_day_id'], ['id'],
        ondelete='CASCADE'
    )

    # Step 8: Drop old race_id foreign key and column from race_results
    op.drop_constraint('race_results_race_id_fkey', 'race_results', type_='foreignkey')
    op.drop_column('race_results', 'race_id')

    # Step 9: Make start_date and end_date non-nullable in races
    op.alter_column('races', 'start_date', nullable=False)
    op.alter_column('races', 'end_date', nullable=False)

    # Step 10: Add check constraint for date range
    op.create_check_constraint(
        'check_race_dates',
        'races',
        'end_date >= start_date'
    )

    # Step 11: Drop race_date and total_participants from races
    op.drop_column('races', 'race_date')
    op.drop_column('races', 'total_participants')


def downgrade():
    # Reverse the migration

    # Step 1: Add back race_date and total_participants to races
    op.add_column('races', sa.Column('race_date', sa.Date(), nullable=True))
    op.add_column('races', sa.Column('total_participants', sa.Integer(), nullable=True))

    # Step 2: Restore race data from race_days (take the first day)
    op.execute("""
        UPDATE races
        SET race_date = race_days.race_date,
            total_participants = race_days.total_participants
        FROM race_days
        WHERE races.id = race_days.race_id
        AND race_days.day_number = 1
    """)

    # Step 3: Make race_date non-nullable
    op.alter_column('races', 'race_date', nullable=False)

    # Step 4: Add race_id column back to race_results
    op.add_column('race_results', sa.Column('race_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Step 5: Restore race_id in race_results from race_days
    op.execute("""
        UPDATE race_results
        SET race_id = race_days.race_id
        FROM race_days
        WHERE race_results.race_day_id = race_days.id
    """)

    # Step 6: Make race_id non-nullable
    op.alter_column('race_results', 'race_id', nullable=False)

    # Step 7: Add back foreign key constraint for race_id
    op.create_foreign_key(
        'race_results_race_id_fkey',
        'race_results', 'races',
        ['race_id'], ['id'],
        ondelete='CASCADE'
    )

    # Step 8: Drop race_day_id foreign key and column
    op.drop_constraint('race_results_race_day_id_fkey', 'race_results', type_='foreignkey')
    op.drop_column('race_results', 'race_day_id')

    # Step 9: Drop race_days table
    op.drop_table('race_days')

    # Step 10: Drop check constraint from races
    op.drop_constraint('check_race_dates', 'races', type_='check')

    # Step 11: Drop start_date and end_date from races
    op.drop_column('races', 'start_date')
    op.drop_column('races', 'end_date')
