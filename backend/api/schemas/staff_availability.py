"""スタッフ出勤可能日のスキーマ定義"""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class StaffAvailabilityBase(BaseModel):
    """基本スキーマ"""
    staff_id: int
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    availability_days: Dict[int, bool] = Field(default_factory=dict)  # {1: True, 2: False, ...}

class StaffAvailabilityCreate(StaffAvailabilityBase):
    """作成用スキーマ"""
    pass

class StaffAvailabilityUpdate(BaseModel):
    """更新用スキーマ"""
    availability_days: Dict[int, bool]

class StaffAvailability(StaffAvailabilityBase):
    """レスポンス用スキーマ"""
    id: int
    created_at: datetime
    updated_at: datetime
    staff_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class MonthlyAvailabilitySummary(BaseModel):
    """月別サマリー"""
    year: int
    month: int
    total_days: int
    available_days: int
    unavailable_days: int
    availability_rate: float