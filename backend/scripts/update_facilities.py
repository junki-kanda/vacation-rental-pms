#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
施設（部屋タイプ）の初期データを作成・更新するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from api.database import engine, SessionLocal
from api.models.property import Facility
from api.models.reservation import Reservation

def update_facilities():
    """施設データを部屋タイプから作成・更新"""
    
    db = SessionLocal()
    
    try:
        # 既存の予約から部屋タイプを収集
        room_types = db.query(Reservation.room_type).distinct().all()
        room_types = [rt[0] for rt in room_types if rt[0]]
        
        print(f"発見された部屋タイプ: {len(room_types)}件")
        
        # 各部屋タイプに対して施設を作成または更新
        for room_type in room_types:
            # 既存の施設を確認
            facility = db.query(Facility).filter(
                (Facility.name == room_type) | 
                (Facility.room_type_identifier == room_type)
            ).first()
            
            if not facility:
                # 新規作成
                facility = Facility(
                    name=room_type,
                    room_type_identifier=room_type,
                    total_rooms=1
                )
                db.add(facility)
                print(f"新規施設作成: {room_type}")
            else:
                # 既存施設の更新
                if not facility.room_type_identifier:
                    facility.room_type_identifier = room_type
                    print(f"施設更新: {facility.name} - room_type_identifier設定")
        
        # 予約データのfacility_idを更新
        reservations = db.query(Reservation).filter(
            Reservation.facility_id == None
        ).all()
        
        updated_count = 0
        for reservation in reservations:
            if reservation.room_type:
                facility = db.query(Facility).filter(
                    (Facility.name == reservation.room_type) | 
                    (Facility.room_type_identifier == reservation.room_type)
                ).first()
                
                if facility:
                    reservation.facility_id = facility.id
                    updated_count += 1
        
        print(f"予約データ更新: {updated_count}件")
        
        db.commit()
        
        # 結果確認
        facilities = db.query(Facility).all()
        print("\n現在の施設一覧:")
        for f in facilities:
            reservation_count = db.query(Reservation).filter(
                Reservation.facility_id == f.id
            ).count()
            print(f"  - {f.name} (ID: {f.id}, 予約数: {reservation_count})")
        
        print("\n処理完了")
        
    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_facilities()