#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全ての清掃タスクを削除するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from api.database import engine, SessionLocal
from api.models.cleaning import CleaningTask, CleaningShift

def delete_all_cleaning_tasks():
    """全ての清掃タスクとシフトを削除"""
    
    db = SessionLocal()
    
    try:
        # まずシフトを削除（外部キー制約があるため）
        shift_count = db.query(CleaningShift).count()
        db.query(CleaningShift).delete()
        print(f"清掃シフト {shift_count}件を削除しました")
        
        # 次にタスクを削除
        task_count = db.query(CleaningTask).count()
        db.query(CleaningTask).delete()
        print(f"清掃タスク {task_count}件を削除しました")
        
        # コミット
        db.commit()
        print("\n[SUCCESS] 全ての清掃タスクとシフトを削除しました")
        
        # 確認
        remaining_tasks = db.query(CleaningTask).count()
        remaining_shifts = db.query(CleaningShift).count()
        print(f"\n削除後の確認:")
        print(f"  残りのタスク数: {remaining_tasks}")
        print(f"  残りのシフト数: {remaining_shifts}")
        
    except Exception as e:
        print(f"[ERROR] エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    response = input("本当に全ての清掃タスクを削除しますか？ (yes/no): ")
    if response.lower() == 'yes':
        delete_all_cleaning_tasks()
    else:
        print("キャンセルしました")