"""add staff groups tables

Revision ID: 004
Revises: 003
Create Date: 2025-01-20 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # スタッフグループテーブル作成
    op.create_table(
        'cleaning_staff_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('can_handle_large_properties', sa.Boolean(), nullable=True),
        sa.Column('can_handle_multiple_properties', sa.Boolean(), nullable=True),
        sa.Column('max_properties_per_day', sa.Integer(), nullable=True),
        sa.Column('available_facilities', sa.JSON(), nullable=True),
        sa.Column('rate_per_property', sa.Float(), nullable=True),
        sa.Column('rate_per_property_with_option', sa.Float(), nullable=True),
        sa.Column('transportation_fee', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_cleaning_staff_groups_id'), 'cleaning_staff_groups', ['id'], unique=False)
    
    # スタッフグループメンバーテーブル作成
    op.create_table(
        'cleaning_staff_group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('staff_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('is_leader', sa.Boolean(), nullable=True),
        sa.Column('joined_date', sa.Date(), nullable=True),
        sa.Column('left_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['cleaning_staff_groups.id'], ),
        sa.ForeignKeyConstraint(['staff_id'], ['cleaning_staff.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cleaning_staff_group_members_id'), 'cleaning_staff_group_members', ['id'], unique=False)
    
    # cleaning_shiftsテーブルにgroup_idカラムを追加（SQLiteのバッチモード使用）
    with op.batch_alter_table('cleaning_shifts') as batch_op:
        batch_op.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_cleaning_shifts_group_id', 'cleaning_staff_groups', ['group_id'], ['id'])
        # staff_idをnullableに変更（グループ割当の場合はstaff_idがNULLになるため）
        batch_op.alter_column('staff_id',
                           existing_type=sa.INTEGER(),
                           nullable=True)


def downgrade():
    # cleaning_shiftsテーブルからgroup_id関連を削除（SQLiteのバッチモード使用）
    with op.batch_alter_table('cleaning_shifts') as batch_op:
        batch_op.drop_constraint('fk_cleaning_shifts_group_id', type_='foreignkey')
        batch_op.drop_column('group_id')
        # staff_idをnon-nullableに戻す
        batch_op.alter_column('staff_id',
                           existing_type=sa.INTEGER(),
                           nullable=False)
    
    # テーブル削除
    op.drop_index(op.f('ix_cleaning_staff_group_members_id'), table_name='cleaning_staff_group_members')
    op.drop_table('cleaning_staff_group_members')
    op.drop_index(op.f('ix_cleaning_staff_groups_id'), table_name='cleaning_staff_groups')
    op.drop_table('cleaning_staff_groups')