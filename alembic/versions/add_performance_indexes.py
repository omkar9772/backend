"""Add performance indexes to all tables

Revision ID: add_indexes_002
Revises: add_race_days_001
Create Date: 2025-12-14

This migration adds indexes to improve query performance across all tables.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_indexes_002'
down_revision = 'add_race_days_001'
branch_labels = None
depends_on = None


def upgrade():
    # ============================================================================
    # USERS TABLE INDEXES
    # ============================================================================
    # Single column indexes
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.create_index('ix_users_phone', 'users', ['phone'], unique=False)
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)
    op.create_index('ix_users_created_at', 'users', ['created_at'], unique=False)

    # Composite indexes
    op.create_index('ix_users_active_created', 'users', ['is_active', 'created_at'], unique=False)

    # ============================================================================
    # ADMIN_USERS TABLE INDEXES
    # ============================================================================
    # Single column indexes
    op.create_index('ix_admin_users_username', 'admin_users', ['username'], unique=False)
    op.create_index('ix_admin_users_email', 'admin_users', ['email'], unique=False)
    op.create_index('ix_admin_users_role', 'admin_users', ['role'], unique=False)
    op.create_index('ix_admin_users_is_active', 'admin_users', ['is_active'], unique=False)
    op.create_index('ix_admin_users_created_at', 'admin_users', ['created_at'], unique=False)

    # Composite indexes
    op.create_index('ix_admin_users_active_role', 'admin_users', ['is_active', 'role'], unique=False)

    # ============================================================================
    # OWNERS TABLE INDEXES
    # ============================================================================
    op.create_index('ix_owners_full_name', 'owners', ['full_name'], unique=False)
    op.create_index('ix_owners_phone_number', 'owners', ['phone_number'], unique=False)
    op.create_index('ix_owners_email', 'owners', ['email'], unique=False)
    op.create_index('ix_owners_created_at', 'owners', ['created_at'], unique=False)

    # ============================================================================
    # BULLS TABLE INDEXES
    # ============================================================================
    # Single column indexes
    op.create_index('ix_bulls_name', 'bulls', ['name'], unique=False)
    op.create_index('ix_bulls_owner_id', 'bulls', ['owner_id'], unique=False)
    op.create_index('ix_bulls_breed', 'bulls', ['breed'], unique=False)
    op.create_index('ix_bulls_is_active', 'bulls', ['is_active'], unique=False)
    op.create_index('ix_bulls_registration_number', 'bulls', ['registration_number'], unique=False)
    op.create_index('ix_bulls_created_at', 'bulls', ['created_at'], unique=False)

    # Composite indexes
    op.create_index('ix_bulls_owner_active', 'bulls', ['owner_id', 'is_active'], unique=False)
    op.create_index('ix_bulls_name_active', 'bulls', ['name', 'is_active'], unique=False)

    # ============================================================================
    # RACES TABLE INDEXES
    # ============================================================================
    # Single column indexes
    op.create_index('ix_races_name', 'races', ['name'], unique=False)
    op.create_index('ix_races_start_date', 'races', ['start_date'], unique=False)
    op.create_index('ix_races_end_date', 'races', ['end_date'], unique=False)
    op.create_index('ix_races_status', 'races', ['status'], unique=False)
    op.create_index('ix_races_created_at', 'races', ['created_at'], unique=False)

    # Composite indexes
    op.create_index('ix_races_status_start_date', 'races', ['status', 'start_date'], unique=False)
    op.create_index('ix_races_dates_range', 'races', ['start_date', 'end_date'], unique=False)

    # ============================================================================
    # RACE_DAYS TABLE INDEXES
    # ============================================================================
    # Single column indexes
    op.create_index('ix_race_days_race_id', 'race_days', ['race_id'], unique=False)
    op.create_index('ix_race_days_day_number', 'race_days', ['day_number'], unique=False)
    op.create_index('ix_race_days_race_date', 'race_days', ['race_date'], unique=False)
    op.create_index('ix_race_days_status', 'race_days', ['status'], unique=False)
    op.create_index('ix_race_days_created_at', 'race_days', ['created_at'], unique=False)

    # Composite indexes
    op.create_index('ix_race_days_race_day_number', 'race_days', ['race_id', 'day_number'], unique=True)
    op.create_index('ix_race_days_race_status', 'race_days', ['race_id', 'status'], unique=False)
    op.create_index('ix_race_days_date_status', 'race_days', ['race_date', 'status'], unique=False)

    # ============================================================================
    # RACE_RESULTS TABLE INDEXES
    # ============================================================================
    # Single column indexes
    op.create_index('ix_race_results_race_day_id', 'race_results', ['race_day_id'], unique=False)
    op.create_index('ix_race_results_bull1_id', 'race_results', ['bull1_id'], unique=False)
    op.create_index('ix_race_results_bull2_id', 'race_results', ['bull2_id'], unique=False)
    op.create_index('ix_race_results_owner1_id', 'race_results', ['owner1_id'], unique=False)
    op.create_index('ix_race_results_owner2_id', 'race_results', ['owner2_id'], unique=False)
    op.create_index('ix_race_results_position', 'race_results', ['position'], unique=False)
    op.create_index('ix_race_results_is_disqualified', 'race_results', ['is_disqualified'], unique=False)
    op.create_index('ix_race_results_created_at', 'race_results', ['created_at'], unique=False)

    # Composite indexes
    op.create_index('ix_race_results_race_day_position', 'race_results', ['race_day_id', 'position'], unique=True)
    op.create_index('ix_race_results_bulls', 'race_results', ['bull1_id', 'bull2_id'], unique=False)
    op.create_index('ix_race_results_owners', 'race_results', ['owner1_id', 'owner2_id'], unique=False)


def downgrade():
    # ============================================================================
    # RACE_RESULTS TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_race_results_owners', table_name='race_results')
    op.drop_index('ix_race_results_bulls', table_name='race_results')
    op.drop_index('ix_race_results_race_day_position', table_name='race_results')
    op.drop_index('ix_race_results_created_at', table_name='race_results')
    op.drop_index('ix_race_results_is_disqualified', table_name='race_results')
    op.drop_index('ix_race_results_position', table_name='race_results')
    op.drop_index('ix_race_results_owner2_id', table_name='race_results')
    op.drop_index('ix_race_results_owner1_id', table_name='race_results')
    op.drop_index('ix_race_results_bull2_id', table_name='race_results')
    op.drop_index('ix_race_results_bull1_id', table_name='race_results')
    op.drop_index('ix_race_results_race_day_id', table_name='race_results')

    # ============================================================================
    # RACE_DAYS TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_race_days_date_status', table_name='race_days')
    op.drop_index('ix_race_days_race_status', table_name='race_days')
    op.drop_index('ix_race_days_race_day_number', table_name='race_days')
    op.drop_index('ix_race_days_created_at', table_name='race_days')
    op.drop_index('ix_race_days_status', table_name='race_days')
    op.drop_index('ix_race_days_race_date', table_name='race_days')
    op.drop_index('ix_race_days_day_number', table_name='race_days')
    op.drop_index('ix_race_days_race_id', table_name='race_days')

    # ============================================================================
    # RACES TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_races_dates_range', table_name='races')
    op.drop_index('ix_races_status_start_date', table_name='races')
    op.drop_index('ix_races_created_at', table_name='races')
    op.drop_index('ix_races_status', table_name='races')
    op.drop_index('ix_races_end_date', table_name='races')
    op.drop_index('ix_races_start_date', table_name='races')
    op.drop_index('ix_races_name', table_name='races')

    # ============================================================================
    # BULLS TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_bulls_name_active', table_name='bulls')
    op.drop_index('ix_bulls_owner_active', table_name='bulls')
    op.drop_index('ix_bulls_created_at', table_name='bulls')
    op.drop_index('ix_bulls_registration_number', table_name='bulls')
    op.drop_index('ix_bulls_is_active', table_name='bulls')
    op.drop_index('ix_bulls_breed', table_name='bulls')
    op.drop_index('ix_bulls_owner_id', table_name='bulls')
    op.drop_index('ix_bulls_name', table_name='bulls')

    # ============================================================================
    # OWNERS TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_owners_created_at', table_name='owners')
    op.drop_index('ix_owners_email', table_name='owners')
    op.drop_index('ix_owners_phone_number', table_name='owners')
    op.drop_index('ix_owners_full_name', table_name='owners')

    # ============================================================================
    # ADMIN_USERS TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_admin_users_active_role', table_name='admin_users')
    op.drop_index('ix_admin_users_created_at', table_name='admin_users')
    op.drop_index('ix_admin_users_is_active', table_name='admin_users')
    op.drop_index('ix_admin_users_role', table_name='admin_users')
    op.drop_index('ix_admin_users_email', table_name='admin_users')
    op.drop_index('ix_admin_users_username', table_name='admin_users')

    # ============================================================================
    # USERS TABLE - DROP INDEXES
    # ============================================================================
    op.drop_index('ix_users_active_created', table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
