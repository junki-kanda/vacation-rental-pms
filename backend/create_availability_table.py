#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スタッフ出勤可能日テーブル作成スクリプト
"""

import sqlite3
import sys
from pathlib import Path

def create_availability_table():
    try:
        # データベースファイルパス
        db_path = Path(__file__).parent / "vacation_rental_pms.db"
        
        if not db_path.exists():
            print(f"データベースファイルが見つかりません: {db_path}")
            return False
        
        # データベース接続
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("スタッフ出勤可能日テーブルの作成を開始します...")
        
        # テーブル作成SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS staff_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day_1 BOOLEAN DEFAULT 1,
            day_2 BOOLEAN DEFAULT 1,
            day_3 BOOLEAN DEFAULT 1,
            day_4 BOOLEAN DEFAULT 1,
            day_5 BOOLEAN DEFAULT 1,
            day_6 BOOLEAN DEFAULT 1,
            day_7 BOOLEAN DEFAULT 1,
            day_8 BOOLEAN DEFAULT 1,
            day_9 BOOLEAN DEFAULT 1,
            day_10 BOOLEAN DEFAULT 1,
            day_11 BOOLEAN DEFAULT 1,
            day_12 BOOLEAN DEFAULT 1,
            day_13 BOOLEAN DEFAULT 1,
            day_14 BOOLEAN DEFAULT 1,
            day_15 BOOLEAN DEFAULT 1,
            day_16 BOOLEAN DEFAULT 1,
            day_17 BOOLEAN DEFAULT 1,
            day_18 BOOLEAN DEFAULT 1,
            day_19 BOOLEAN DEFAULT 1,
            day_20 BOOLEAN DEFAULT 1,
            day_21 BOOLEAN DEFAULT 1,
            day_22 BOOLEAN DEFAULT 1,
            day_23 BOOLEAN DEFAULT 1,
            day_24 BOOLEAN DEFAULT 1,
            day_25 BOOLEAN DEFAULT 1,
            day_26 BOOLEAN DEFAULT 1,
            day_27 BOOLEAN DEFAULT 1,
            day_28 BOOLEAN DEFAULT 1,
            day_29 BOOLEAN DEFAULT 1,
            day_30 BOOLEAN DEFAULT 1,
            day_31 BOOLEAN DEFAULT 1,
            created_at DATE DEFAULT CURRENT_TIMESTAMP,
            updated_at DATE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES cleaning_staff(id),
            UNIQUE(staff_id, year, month)
        )
        """
        
        cursor.execute(create_table_sql)
        print("[OK] staff_availabilityテーブルを作成しました")
        
        # インデックス作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_staff_availability_year_month 
            ON staff_availability(year, month)
        """)
        print("[OK] インデックスを作成しました")
        
        # 変更をコミット
        conn.commit()
        print("[SUCCESS] スタッフ出勤可能日テーブルの作成が完了しました！")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = create_availability_table()
    sys.exit(0 if success else 1)