#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix staff_id nullable constraint in cleaning_shifts table"""

import sqlite3
import os

def fix_staff_id_nullable():
    db_path = 'vacation_rental_pms.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return
    
    # SQLiteでは直接カラムのNULL制約を変更できないため、
    # テーブルを再作成する必要がある
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 既存データをバックアップ
        cursor.execute("SELECT * FROM cleaning_shifts")
        existing_data = cursor.fetchall()
        
        # 既存テーブルの構造を取得
        cursor.execute("PRAGMA table_info(cleaning_shifts)")
        columns = cursor.fetchall()
        
        print(f"Found {len(existing_data)} existing shifts")
        print("Current table structure:")
        for col in columns:
            print(f"  {col[1]}: {col[2]} - NOT NULL: {bool(col[3])}")
        
        # 既存テーブルを削除
        cursor.execute("DROP TABLE IF EXISTS cleaning_shifts_old")
        cursor.execute("ALTER TABLE cleaning_shifts RENAME TO cleaning_shifts_old")
        
        # 新しいテーブルを作成（staff_idをNULLABLEに）
        create_table_sql = """
        CREATE TABLE cleaning_shifts (
            id INTEGER PRIMARY KEY,
            staff_id INTEGER NULL REFERENCES cleaning_staff(id),
            group_id INTEGER NULL REFERENCES cleaning_staff_groups(id),
            task_id INTEGER NOT NULL REFERENCES cleaning_tasks(id),
            assigned_date DATE NOT NULL,
            scheduled_start_time TIME NOT NULL,
            scheduled_end_time TIME NOT NULL,
            status VARCHAR(11) NOT NULL,
            actual_start_time DATETIME,
            actual_end_time DATETIME,
            check_in_location JSON,
            check_out_location JSON,
            calculated_wage FLOAT,
            is_option_included INTEGER,
            num_assigned_staff INTEGER,
            transportation_fee FLOAT,
            bonus FLOAT,
            total_payment FLOAT,
            performance_rating INTEGER,
            performance_notes TEXT,
            notes TEXT,
            cancellation_reason TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            created_by VARCHAR(100)
        )
        """
        
        cursor.execute(create_table_sql)
        
        # インデックスを再作成
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_cleaning_shifts_id ON cleaning_shifts (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_cleaning_shifts_assigned_date ON cleaning_shifts (assigned_date)")
        
        # データを復元
        if existing_data:
            placeholders = ','.join(['?' for _ in range(len(columns))])
            insert_sql = f"INSERT INTO cleaning_shifts VALUES ({placeholders})"
            cursor.executemany(insert_sql, existing_data)
            print(f"Restored {len(existing_data)} shift records")
        
        # 古いテーブルを削除
        cursor.execute("DROP TABLE cleaning_shifts_old")
        
        conn.commit()
        print("Successfully updated cleaning_shifts table - staff_id is now nullable")
        
        # 新しい構造を確認
        cursor.execute("PRAGMA table_info(cleaning_shifts)")
        new_columns = cursor.fetchall()
        print("New table structure:")
        for col in new_columns:
            print(f"  {col[1]}: {col[2]} - NOT NULL: {bool(col[3])}")
            
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_staff_id_nullable()