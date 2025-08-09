#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
データベーススキーマ更新スクリプト
清掃スタッフテーブルに新しい報酬カラムを追加
"""

import sqlite3
import sys
from pathlib import Path

def update_database():
    try:
        # データベースファイルパス
        db_path = Path(__file__).parent / "vacation_rental_pms.db"
        
        if not db_path.exists():
            print(f"データベースファイルが見つかりません: {db_path}")
            return False
        
        # データベース接続
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("データベーススキーマの更新を開始します...")
        
        # 現在のテーブル構造を確認
        cursor.execute("PRAGMA table_info(cleaning_staff)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 必要なカラムが存在するか確認
        columns_to_add = []
        
        if 'rate_per_property' not in column_names:
            columns_to_add.append(('rate_per_property', 'REAL DEFAULT 3000'))
        
        if 'rate_per_property_with_option' not in column_names:
            columns_to_add.append(('rate_per_property_with_option', 'REAL DEFAULT 4000'))
        
        # カラムを追加
        for column_name, column_def in columns_to_add:
            try:
                alter_sql = f"ALTER TABLE cleaning_staff ADD COLUMN {column_name} {column_def}"
                cursor.execute(alter_sql)
                print(f"[OK] カラム '{column_name}' を追加しました")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"- カラム '{column_name}' は既に存在します")
                else:
                    raise
        
        # 既存のhourly_rateカラムからデータを移行（存在する場合）
        if 'hourly_rate' in column_names and 'rate_per_property' not in column_names:
            print("既存の時給データを1棟あたり報酬に変換中...")
            cursor.execute("""
                UPDATE cleaning_staff 
                SET rate_per_property = CASE 
                    WHEN hourly_rate > 0 THEN hourly_rate * 2
                    ELSE 3000
                END,
                rate_per_property_with_option = CASE 
                    WHEN hourly_rate > 0 THEN hourly_rate * 2.5
                    ELSE 4000
                END
                WHERE rate_per_property IS NULL
            """)
            print("[OK] データ移行完了")
        
        # cleaning_shiftsテーブルの更新
        cursor.execute("PRAGMA table_info(cleaning_shifts)")
        shift_columns = cursor.fetchall()
        shift_column_names = [col[1] for col in shift_columns]
        
        shift_columns_to_add = []
        
        if 'is_option_included' not in shift_column_names:
            shift_columns_to_add.append(('is_option_included', 'INTEGER DEFAULT 0'))
        
        if 'num_assigned_staff' not in shift_column_names:
            shift_columns_to_add.append(('num_assigned_staff', 'INTEGER DEFAULT 1'))
        
        # シフトテーブルにカラムを追加
        for column_name, column_def in shift_columns_to_add:
            try:
                alter_sql = f"ALTER TABLE cleaning_shifts ADD COLUMN {column_name} {column_def}"
                cursor.execute(alter_sql)
                print(f"[OK] cleaning_shifts テーブルに '{column_name}' カラムを追加しました")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"- cleaning_shifts テーブルの '{column_name}' カラムは既に存在します")
                else:
                    raise
        
        # 変更をコミット
        conn.commit()
        print("\n[SUCCESS] データベーススキーマの更新が完了しました！")
        
        # 更新後の構造を表示
        print("\n現在のcleaning_staffテーブル構造:")
        cursor.execute("PRAGMA table_info(cleaning_staff)")
        for col in cursor.fetchall():
            if col[1] in ['rate_per_property', 'rate_per_property_with_option', 'transportation_fee']:
                print(f"  - {col[1]}: {col[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = update_database()
    sys.exit(0 if success else 1)