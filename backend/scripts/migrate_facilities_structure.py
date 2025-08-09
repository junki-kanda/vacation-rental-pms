#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
施設データベース構造を新しい形式に移行するスクリプト
施設名を部屋タイプ名と一致させ、施設グループを追加
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from api.database import engine, SessionLocal
from api.models.property import Facility
from api.models.reservation import Reservation

def migrate_facilities_structure():
    """施設データベース構造を新しい形式に移行"""
    
    db = SessionLocal()
    
    try:
        print("=== 施設データベース構造移行開始 ===\n")
        
        # 1. まず既存の施設データを確認
        existing_facilities = db.query(Facility).all()
        print(f"既存施設数: {len(existing_facilities)}件")
        
        # 2. 予約データから全ての部屋タイプを収集
        room_types = db.query(Reservation.room_type).distinct().all()
        room_types = [rt[0] for rt in room_types if rt[0]]
        print(f"予約データの部屋タイプ数: {len(room_types)}件")
        print(f"部屋タイプ一覧: {room_types}\n")
        
        # 3. 既存施設を削除して新しい構造で作成
        print("施設データを新しい構造で再作成します...")
        
        # 既存施設を全て削除
        db.query(Facility).delete()
        
        # 4. 部屋タイプごとに新しい施設を作成
        facilities_created = []
        for room_type in room_types:
            # 施設グループを判定
            facility_group = None
            if "Villa" in room_type or "villa" in room_type:
                facility_group = "Villa"
            elif "別荘" in room_type:
                facility_group = "別荘"
            elif "コテージ" in room_type:
                facility_group = "コテージ"
            elif "貸別荘" in room_type:
                facility_group = "貸別荘"
            
            # 新しい施設を作成
            new_facility = Facility(
                name=room_type,  # 施設名 = 部屋タイプ名
                facility_group=facility_group,
                is_active=True,
                cleaning_fee=10000.0,  # デフォルト値
                base_rate=30000.0,  # デフォルト値
                max_guests=6,  # デフォルト値
                bedrooms=2,  # デフォルト値
                bathrooms=1  # デフォルト値
            )
            
            # 特定の施設に応じた設定
            if "Villa A棟" in room_type:
                new_facility.max_guests = 8
                new_facility.bedrooms = 3
                new_facility.bathrooms = 2
                new_facility.cleaning_fee = 15000.0
            elif "Villa B棟" in room_type:
                new_facility.max_guests = 6
                new_facility.bedrooms = 2
                new_facility.bathrooms = 1
                new_facility.cleaning_fee = 12000.0
            elif "貸別荘風の詩603" in room_type:
                new_facility.max_guests = 4
                new_facility.bedrooms = 1
                new_facility.bathrooms = 1
                new_facility.cleaning_fee = 8000.0
            
            db.add(new_facility)
            facilities_created.append(new_facility)
            print(f"  施設作成: {room_type} (グループ: {facility_group or '未設定'})")
        
        db.flush()
        
        # 5. 予約データのfacility_idを更新
        print("\n予約データのfacility_idを更新中...")
        reservations = db.query(Reservation).all()
        updated_count = 0
        
        for reservation in reservations:
            if reservation.room_type:
                # 部屋タイプに一致する施設を検索
                facility = db.query(Facility).filter(
                    Facility.name == reservation.room_type
                ).first()
                
                if facility and reservation.facility_id != facility.id:
                    old_id = reservation.facility_id
                    reservation.facility_id = facility.id
                    updated_count += 1
                    if updated_count <= 10:  # 最初の10件だけ表示
                        print(f"  予約ID {reservation.id}: 施設ID {old_id} → {facility.id} ({facility.name})")
        
        if updated_count > 10:
            print(f"  ... 他 {updated_count - 10}件")
        
        print(f"\n合計 {updated_count}件の予約を更新しました")
        
        # 6. 清掃タスクのfacility_idも更新
        from api.models.cleaning import CleaningTask
        cleaning_tasks = db.query(CleaningTask).all()
        task_updated_count = 0
        
        for task in cleaning_tasks:
            # タスクに関連する予約から施設IDを取得
            if task.reservation_id:
                reservation = db.query(Reservation).filter(
                    Reservation.id == task.reservation_id
                ).first()
                if reservation and reservation.facility_id:
                    if task.facility_id != reservation.facility_id:
                        old_id = task.facility_id
                        task.facility_id = reservation.facility_id
                        task_updated_count += 1
        
        print(f"清掃タスク {task_updated_count}件の施設IDを更新しました")
        
        # コミット
        db.commit()
        
        # 7. 結果確認
        print("\n=== 移行結果 ===")
        facilities = db.query(Facility).all()
        print(f"\n新しい施設一覧 ({len(facilities)}件):")
        for f in facilities:
            reservation_count = db.query(Reservation).filter(
                Reservation.facility_id == f.id
            ).count()
            print(f"  ID:{f.id} | 名前:{f.name} | グループ:{f.facility_group or '未設定'} | 予約数:{reservation_count}")
        
        # 8. 施設グループごとの集計
        print("\n施設グループ別集計:")
        groups = db.query(Facility.facility_group).distinct().all()
        for group in groups:
            group_name = group[0] or "未設定"
            count = db.query(Facility).filter(
                Facility.facility_group == group[0]
            ).count()
            print(f"  {group_name}: {count}件")
        
        print("\n[SUCCESS] 施設データベース構造の移行が完了しました")
        
    except Exception as e:
        print(f"[ERROR] エラーが発生しました: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    response = input("施設データベース構造を新しい形式に移行します。既存のデータは更新されます。続行しますか？ (yes/no): ")
    if response.lower() == 'yes':
        migrate_facilities_structure()
    else:
        print("キャンセルしました")