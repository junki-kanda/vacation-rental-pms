#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
予約データのfacility_idを部屋タイプから設定
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from api.database import engine, SessionLocal
from api.models.property import Facility
from api.models.reservation import Reservation

def fix_reservation_facilities():
    """予約データのfacility_idを修正"""
    
    db = SessionLocal()
    
    try:
        # facility_idがNullまたは誤った予約を取得
        reservations = db.query(Reservation).all()
        
        updated_count = 0
        for reservation in reservations:
            if reservation.room_type:
                # room_typeに一致する施設を検索
                facility = db.query(Facility).filter(
                    (Facility.name == reservation.room_type) | 
                    (Facility.room_type_identifier == reservation.room_type)
                ).first()
                
                if facility:
                    # facility_idが異なる場合のみ更新
                    if reservation.facility_id != facility.id:
                        old_id = reservation.facility_id
                        reservation.facility_id = facility.id
                        updated_count += 1
                        print(f"予約ID {reservation.id}: 施設ID {old_id} → {facility.id} ({facility.name})")
        
        db.commit()
        print(f"\n合計 {updated_count}件の予約を更新しました")
        
        # 結果確認
        print("\n施設別予約数:")
        facilities = db.query(Facility).all()
        for f in facilities:
            count = db.query(Reservation).filter(
                Reservation.facility_id == f.id
            ).count()
            print(f"  {f.name}: {count}件")
        
    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_reservation_facilities()