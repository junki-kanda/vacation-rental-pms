"""
データベースマイグレーションスクリプト
新しいカラムを追加してデータベースを更新
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from api.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """データベースに新しいカラムを追加"""
    
    # データベース接続
    engine = create_engine("sqlite:///vacation_rental_pms.db")
    
    # 新しいカラムのリスト
    new_columns = [
        ("nights", "INTEGER DEFAULT 1"),
        ("rooms", "INTEGER DEFAULT 1"),
        ("meal_plan", "VARCHAR(100)"),
        ("payment_method", "VARCHAR(100)"),
        ("booker_name", "VARCHAR(100)"),
        ("booker_name_kana", "VARCHAR(100)"),
        ("plan_name", "VARCHAR(200)"),
        ("plan_code", "VARCHAR(50)"),
        ("checkin_time", "VARCHAR(10)"),
        ("cancel_date", "DATE")
    ]
    
    with engine.connect() as conn:
        # 現在のカラムを確認
        result = conn.execute(text("PRAGMA table_info(reservations)"))
        existing_columns = [row[1] for row in result]
        
        # 新しいカラムを追加
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE reservations ADD COLUMN {column_name} {column_type}"
                    conn.execute(text(alter_sql))
                    conn.commit()
                    logger.info(f"カラム追加成功: {column_name}")
                except Exception as e:
                    logger.warning(f"カラム追加スキップ（既存）: {column_name} - {e}")
            else:
                logger.info(f"カラム既存: {column_name}")
    
    # テーブル全体を再作成（必要に応じて）
    Base.metadata.create_all(bind=engine)
    logger.info("データベースマイグレーション完了")

def verify_migration():
    """マイグレーション結果を確認"""
    engine = create_engine("sqlite:///vacation_rental_pms.db")
    
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(reservations)"))
        columns = result.fetchall()
        
        print("\n現在のreservationsテーブルのカラム:")
        for col in columns:
            print(f"  {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL'}")

if __name__ == "__main__":
    print("データベースマイグレーションを開始します...")
    migrate_database()
    verify_migration()
    print("\nマイグレーション完了！")