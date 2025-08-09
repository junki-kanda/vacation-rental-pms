"""Update facilities structure - facility name equals room type

Revision ID: 003
Revises: 002
Create Date: 2025-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """施設テーブルの構造を更新"""
    
    # 新しいカラムを追加
    with op.batch_alter_table('facilities', schema=None) as batch_op:
        # facility_groupカラムを追加
        batch_op.add_column(sa.Column('facility_group', sa.String(100), nullable=True))
        # その他の新しいカラムを追加
        batch_op.add_column(sa.Column('cleaning_fee', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('base_rate', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('max_guests', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('bedrooms', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('bathrooms', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))
        
    # デフォルト値を設定
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE facilities 
        SET max_guests = 4,
            bedrooms = 1,
            bathrooms = 1,
            is_active = 1,
            cleaning_fee = 10000.0,
            base_rate = 30000.0
        WHERE max_guests IS NULL
    """))
    
    # 既存の room_type_identifier カラムを削除（もし存在すれば）
    try:
        with op.batch_alter_table('facilities', schema=None) as batch_op:
            batch_op.drop_column('room_type_identifier')
    except:
        pass  # カラムが存在しない場合は無視
    
    try:
        with op.batch_alter_table('facilities', schema=None) as batch_op:
            batch_op.drop_column('total_rooms')
    except:
        pass  # カラムが存在しない場合は無視


def downgrade():
    """ロールバック処理"""
    
    with op.batch_alter_table('facilities', schema=None) as batch_op:
        # 新しいカラムを削除
        batch_op.drop_column('facility_group')
        batch_op.drop_column('cleaning_fee')
        batch_op.drop_column('base_rate')
        batch_op.drop_column('max_guests')
        batch_op.drop_column('bedrooms')
        batch_op.drop_column('bathrooms')
        batch_op.drop_column('is_active')
        
        # 古いカラムを復元
        batch_op.add_column(sa.Column('room_type_identifier', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('total_rooms', sa.Integer(), nullable=True))