#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
メールカラムの制約を修正するスクリプト
空のメールアドレスをNULLに変更し、UNIQUE制約を維持
"""

import sqlite3
import sys
from pathlib import Path

def fix_email_constraint():
    try:
        # データベースファイルパス
        db_path = Path(__file__).parent / "vacation_rental_pms.db"
        
        if not db_path.exists():
            print(f"データベースファイルが見つかりません: {db_path}")
            return False
        
        # データベース接続
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("メールカラムの制約修正を開始します...")
        
        # 既存の空文字列のemailをNULLに更新
        cursor.execute("""
            UPDATE cleaning_staff 
            SET email = NULL 
            WHERE email = '' OR email IS NULL
        """)
        updated_rows = cursor.rowcount
        print(f"[OK] {updated_rows}件のレコードのemailをNULLに更新しました")
        
        # 変更をコミット
        conn.commit()
        print("[SUCCESS] メールカラムの制約修正が完了しました！")
        
        # 現在のデータを確認
        cursor.execute("""
            SELECT id, name, email 
            FROM cleaning_staff 
            ORDER BY id
        """)
        
        print("\n現在のスタッフデータ:")
        for row in cursor.fetchall():
            email_display = row[2] if row[2] else "(なし)"
            print(f"  ID: {row[0]}, 名前: {row[1]}, Email: {email_display}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] エラーが発生しました: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = fix_email_constraint()
    sys.exit(0 if success else 1)