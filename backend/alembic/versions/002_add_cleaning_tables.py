"""add cleaning tables

Revision ID: 002
Revises: 001
Create Date: 2025-08-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import json

# revision identifiers, used by Alembic.
revision = '002'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create cleaning_staff table
    op.create_table('cleaning_staff',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_kana', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('skill_level', sa.Integer(), nullable=True),
        sa.Column('can_drive', sa.Boolean(), nullable=True),
        sa.Column('has_car', sa.Boolean(), nullable=True),
        sa.Column('available_facilities', sa.JSON(), nullable=True),
        sa.Column('available_schedule', sa.JSON(), nullable=True),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('transportation_fee', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_cleaning_staff_id'), 'cleaning_staff', ['id'], unique=False)

    # Create cleaning_tasks table
    op.create_table('cleaning_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reservation_id', sa.Integer(), nullable=False),
        sa.Column('facility_id', sa.Integer(), nullable=False),
        sa.Column('checkout_date', sa.Date(), nullable=False),
        sa.Column('checkout_time', sa.Time(), nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_start_time', sa.Time(), nullable=True),
        sa.Column('scheduled_end_time', sa.Time(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('UNASSIGNED', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'VERIFIED', 'CANCELLED', name='taskstatus'), nullable=False),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('verified_by', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('supplies_needed', sa.JSON(), nullable=True),
        sa.Column('photos_before', sa.JSON(), nullable=True),
        sa.Column('photos_after', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ),
        sa.ForeignKeyConstraint(['reservation_id'], ['reservations.id'], ),
        sa.ForeignKeyConstraint(['verified_by'], ['cleaning_staff.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cleaning_tasks_checkout_date'), 'cleaning_tasks', ['checkout_date'], unique=False)
    op.create_index(op.f('ix_cleaning_tasks_id'), 'cleaning_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_cleaning_tasks_scheduled_date'), 'cleaning_tasks', ['scheduled_date'], unique=False)

    # Create cleaning_shifts table
    op.create_table('cleaning_shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('staff_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('assigned_date', sa.Date(), nullable=False),
        sa.Column('scheduled_start_time', sa.Time(), nullable=False),
        sa.Column('scheduled_end_time', sa.Time(), nullable=False),
        sa.Column('status', sa.Enum('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='shiftstatus'), nullable=False),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('check_in_location', sa.JSON(), nullable=True),
        sa.Column('check_out_location', sa.JSON(), nullable=True),
        sa.Column('calculated_wage', sa.Float(), nullable=True),
        sa.Column('transportation_fee', sa.Float(), nullable=True),
        sa.Column('bonus', sa.Float(), nullable=True),
        sa.Column('total_payment', sa.Float(), nullable=True),
        sa.Column('performance_rating', sa.Integer(), nullable=True),
        sa.Column('performance_notes', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['staff_id'], ['cleaning_staff.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['cleaning_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cleaning_shifts_assigned_date'), 'cleaning_shifts', ['assigned_date'], unique=False)
    op.create_index(op.f('ix_cleaning_shifts_id'), 'cleaning_shifts', ['id'], unique=False)

    # Create facility_cleaning_settings table
    op.create_table('facility_cleaning_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('facility_id', sa.Integer(), nullable=False),
        sa.Column('standard_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('deep_cleaning_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('minimum_interval_hours', sa.Integer(), nullable=True),
        sa.Column('cleaning_checklist', sa.JSON(), nullable=True),
        sa.Column('required_supplies', sa.JSON(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('access_instructions', sa.Text(), nullable=True),
        sa.Column('parking_info', sa.Text(), nullable=True),
        sa.Column('preferred_staff_ids', sa.JSON(), nullable=True),
        sa.Column('cleaning_fee', sa.Float(), nullable=True),
        sa.Column('staff_payment', sa.Float(), nullable=True),
        sa.Column('requires_inspection', sa.Boolean(), nullable=True),
        sa.Column('auto_assign', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['facility_id'], ['facilities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('facility_id')
    )
    op.create_index(op.f('ix_facility_cleaning_settings_id'), 'facility_cleaning_settings', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_facility_cleaning_settings_id'), table_name='facility_cleaning_settings')
    op.drop_table('facility_cleaning_settings')
    
    op.drop_index(op.f('ix_cleaning_shifts_id'), table_name='cleaning_shifts')
    op.drop_index(op.f('ix_cleaning_shifts_assigned_date'), table_name='cleaning_shifts')
    op.drop_table('cleaning_shifts')
    
    op.drop_index(op.f('ix_cleaning_tasks_scheduled_date'), table_name='cleaning_tasks')
    op.drop_index(op.f('ix_cleaning_tasks_id'), table_name='cleaning_tasks')
    op.drop_index(op.f('ix_cleaning_tasks_checkout_date'), table_name='cleaning_tasks')
    op.drop_table('cleaning_tasks')
    
    op.drop_index(op.f('ix_cleaning_staff_id'), table_name='cleaning_staff')
    op.drop_table('cleaning_staff')
    
    # Drop enums
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='shiftstatus').drop(op.get_bind(), checkfirst=False)