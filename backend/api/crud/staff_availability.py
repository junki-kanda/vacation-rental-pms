"""スタッフ出勤可能日のCRUD操作"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Dict
from datetime import datetime
import calendar

from ..models.staff_availability import StaffAvailability as StaffAvailabilityModel
from ..schemas.staff_availability import (
    StaffAvailabilityCreate,
    StaffAvailabilityUpdate
)

def get_staff_availability(
    db: Session,
    staff_id: int,
    year: int,
    month: int
) -> Optional[StaffAvailabilityModel]:
    """特定スタッフの特定年月の出勤可能日を取得"""
    return db.query(StaffAvailabilityModel).filter(
        and_(
            StaffAvailabilityModel.staff_id == staff_id,
            StaffAvailabilityModel.year == year,
            StaffAvailabilityModel.month == month
        )
    ).first()

def get_staff_availabilities_by_month(
    db: Session,
    year: int,
    month: int
) -> List[StaffAvailabilityModel]:
    """特定年月の全スタッフの出勤可能日を取得"""
    return db.query(StaffAvailabilityModel).filter(
        and_(
            StaffAvailabilityModel.year == year,
            StaffAvailabilityModel.month == month
        )
    ).all()

def create_or_update_staff_availability(
    db: Session,
    availability: StaffAvailabilityCreate
) -> StaffAvailabilityModel:
    """スタッフの出勤可能日を作成または更新"""
    
    # 既存レコードを確認
    existing = get_staff_availability(
        db, 
        availability.staff_id,
        availability.year,
        availability.month
    )
    
    if existing:
        # 更新
        for day, is_available in availability.availability_days.items():
            day_column = f"day_{day}"
            if hasattr(existing, day_column):
                setattr(existing, day_column, is_available)
        
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # 新規作成
        db_availability = StaffAvailabilityModel(
            staff_id=availability.staff_id,
            year=availability.year,
            month=availability.month
        )
        
        # 各日の設定
        for day, is_available in availability.availability_days.items():
            day_column = f"day_{day}"
            if hasattr(db_availability, day_column):
                setattr(db_availability, day_column, is_available)
        
        db.add(db_availability)
        db.commit()
        db.refresh(db_availability)
        return db_availability

def update_staff_availability(
    db: Session,
    staff_id: int,
    year: int,
    month: int,
    update_data: StaffAvailabilityUpdate
) -> Optional[StaffAvailabilityModel]:
    """スタッフの出勤可能日を更新"""
    
    db_availability = get_staff_availability(db, staff_id, year, month)
    if not db_availability:
        return None
    
    # 各日の更新
    for day, is_available in update_data.availability_days.items():
        day_column = f"day_{day}"
        if hasattr(db_availability, day_column):
            setattr(db_availability, day_column, is_available)
    
    db_availability.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_availability)
    return db_availability

def get_available_staff_for_date(
    db: Session,
    year: int,
    month: int,
    day: int
) -> List[int]:
    """特定日に出勤可能なスタッフIDのリストを取得"""
    
    day_column = f"day_{day}"
    availabilities = db.query(StaffAvailabilityModel).filter(
        and_(
            StaffAvailabilityModel.year == year,
            StaffAvailabilityModel.month == month,
            getattr(StaffAvailabilityModel, day_column) == True
        )
    ).all()
    
    return [avail.staff_id for avail in availabilities]

def convert_model_to_dict(availability: StaffAvailabilityModel) -> Dict:
    """モデルをdictionary形式に変換"""
    
    # 該当月の日数を取得
    _, days_in_month = calendar.monthrange(availability.year, availability.month)
    
    availability_days = {}
    for day in range(1, days_in_month + 1):
        day_column = f"day_{day}"
        if hasattr(availability, day_column):
            availability_days[day] = getattr(availability, day_column)
    
    return {
        "id": availability.id,
        "staff_id": availability.staff_id,
        "year": availability.year,
        "month": availability.month,
        "availability_days": availability_days,
        "created_at": availability.created_at,
        "updated_at": availability.updated_at
    }

def initialize_month_availability(
    db: Session,
    staff_id: int,
    year: int,
    month: int,
    default_available: bool = True
) -> StaffAvailabilityModel:
    """月の出勤可能日を初期化"""
    
    _, days_in_month = calendar.monthrange(year, month)
    
    availability_days = {
        day: default_available for day in range(1, days_in_month + 1)
    }
    
    availability_create = StaffAvailabilityCreate(
        staff_id=staff_id,
        year=year,
        month=month,
        availability_days=availability_days
    )
    
    return create_or_update_staff_availability(db, availability_create)