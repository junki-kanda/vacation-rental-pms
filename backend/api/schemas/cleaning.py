"""清掃管理機能のPydanticスキーマ定義"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum

class TaskStatus(str, Enum):
    """清掃タスクのステータス"""
    UNASSIGNED = "unassigned"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"

class ShiftStatus(str, Enum):
    """シフトのステータス"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# スタッフ関連のスキーマ
class StaffBase(BaseModel):
    """スタッフ基本情報"""
    name: str = Field(..., min_length=1, max_length=100)
    name_kana: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    skill_level: int = Field(default=1, ge=1, le=5)
    can_drive: bool = False
    has_car: bool = False
    available_facilities: List[int] = []
    available_schedule: Dict[str, Dict[str, str]] = {}
    rate_per_property: float = Field(default=3000, ge=0)
    rate_per_property_with_option: float = Field(default=4000, ge=0)
    transportation_fee: float = Field(default=0, ge=0)
    is_active: bool = True
    notes: Optional[str] = None

class StaffCreate(StaffBase):
    """スタッフ作成用スキーマ"""
    pass

class StaffUpdate(BaseModel):
    """スタッフ更新用スキーマ"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    name_kana: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    skill_level: Optional[int] = Field(None, ge=1, le=5)
    can_drive: Optional[bool] = None
    has_car: Optional[bool] = None
    available_facilities: Optional[List[int]] = None
    available_schedule: Optional[Dict[str, Dict[str, str]]] = None
    rate_per_property: Optional[float] = Field(None, ge=0)
    rate_per_property_with_option: Optional[float] = Field(None, ge=0)
    transportation_fee: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class Staff(StaffBase):
    """スタッフ情報（レスポンス用）"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 清掃タスク関連のスキーマ
class CleaningTaskBase(BaseModel):
    """清掃タスク基本情報"""
    reservation_id: int
    facility_id: int
    checkout_date: date
    checkout_time: Optional[time] = None
    scheduled_date: date
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    estimated_duration_minutes: int = Field(default=120, ge=0)
    priority: int = Field(default=3, ge=1, le=5)
    special_instructions: Optional[str] = None
    supplies_needed: Optional[List[str]] = []

class CleaningTaskCreate(CleaningTaskBase):
    """清掃タスク作成用スキーマ"""
    pass

class CleaningTaskUpdate(BaseModel):
    """清掃タスク更新用スキーマ"""
    scheduled_date: Optional[date] = None
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[TaskStatus] = None
    special_instructions: Optional[str] = None
    supplies_needed: Optional[List[str]] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    verification_notes: Optional[str] = None

class CleaningTask(CleaningTaskBase):
    """清掃タスク情報（レスポンス用）"""
    id: int
    status: TaskStatus
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    photos_before: Optional[List[str]] = []
    photos_after: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
    
    # リレーション情報
    assigned_staff: Optional[List["Staff"]] = []
    facility_name: Optional[str] = None
    guest_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# シフト関連のスキーマ
class CleaningShiftBase(BaseModel):
    """シフト基本情報"""
    staff_id: int
    task_id: int
    assigned_date: date
    scheduled_start_time: time
    scheduled_end_time: time
    is_option_included: bool = False
    notes: Optional[str] = None

class CleaningShiftCreate(CleaningShiftBase):
    """シフト作成用スキーマ"""
    created_by: Optional[str] = None

class CleaningShiftUpdate(BaseModel):
    """シフト更新用スキーマ"""
    assigned_date: Optional[date] = None
    scheduled_start_time: Optional[time] = None
    scheduled_end_time: Optional[time] = None
    status: Optional[ShiftStatus] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    check_in_location: Optional[Dict[str, float]] = None
    check_out_location: Optional[Dict[str, float]] = None
    performance_rating: Optional[int] = Field(None, ge=1, le=5)
    performance_notes: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

class CleaningShift(CleaningShiftBase):
    """シフト情報（レスポンス用）"""
    id: int
    status: ShiftStatus
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    check_in_location: Optional[Dict[str, float]] = None
    check_out_location: Optional[Dict[str, float]] = None
    calculated_wage: Optional[float] = None
    is_option_included: bool = False
    num_assigned_staff: int = 1
    transportation_fee: Optional[float] = None
    bonus: Optional[float] = None
    total_payment: Optional[float] = None
    performance_rating: Optional[int] = None
    performance_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    # リレーション情報
    staff_name: Optional[str] = None
    facility_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# 施設清掃設定関連のスキーマ
class FacilityCleaningSettingsBase(BaseModel):
    """施設清掃設定基本情報"""
    facility_id: int
    standard_duration_minutes: int = Field(default=120, ge=0)
    deep_cleaning_duration_minutes: int = Field(default=180, ge=0)
    minimum_interval_hours: int = Field(default=2, ge=0)
    cleaning_checklist: List[Dict[str, Any]] = []
    required_supplies: List[str] = []
    special_instructions: Optional[str] = None
    access_instructions: Optional[str] = None
    parking_info: Optional[str] = None
    preferred_staff_ids: List[int] = []
    cleaning_fee: Optional[float] = Field(None, ge=0)
    staff_payment: Optional[float] = Field(None, ge=0)
    requires_inspection: bool = False
    auto_assign: bool = True

class FacilityCleaningSettingsCreate(FacilityCleaningSettingsBase):
    """施設清掃設定作成用スキーマ"""
    pass

class FacilityCleaningSettingsUpdate(BaseModel):
    """施設清掃設定更新用スキーマ"""
    standard_duration_minutes: Optional[int] = Field(None, ge=0)
    deep_cleaning_duration_minutes: Optional[int] = Field(None, ge=0)
    minimum_interval_hours: Optional[int] = Field(None, ge=0)
    cleaning_checklist: Optional[List[Dict[str, Any]]] = None
    required_supplies: Optional[List[str]] = None
    special_instructions: Optional[str] = None
    access_instructions: Optional[str] = None
    parking_info: Optional[str] = None
    preferred_staff_ids: Optional[List[int]] = None
    cleaning_fee: Optional[float] = Field(None, ge=0)
    staff_payment: Optional[float] = Field(None, ge=0)
    requires_inspection: Optional[bool] = None
    auto_assign: Optional[bool] = None

class FacilityCleaningSettings(FacilityCleaningSettingsBase):
    """施設清掃設定情報（レスポンス用）"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # リレーション情報
    facility_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# 集計・ダッシュボード用スキーマ
class CleaningDashboardStats(BaseModel):
    """清掃ダッシュボード統計"""
    today_tasks: int
    unassigned_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    active_staff: int
    average_completion_time: Optional[float] = None
    
class StaffPerformance(BaseModel):
    """スタッフパフォーマンス"""
    staff_id: int
    staff_name: str
    completed_tasks: int
    average_rating: Optional[float] = None
    total_hours: float
    total_earnings: float

class TaskAutoAssignRequest(BaseModel):
    """タスク自動割当リクエスト"""
    task_ids: List[int]
    date: date
    consider_skills: bool = True
    consider_distance: bool = True
    consider_availability: bool = True

class TaskAutoAssignResponse(BaseModel):
    """タスク自動割当レスポンス"""
    success: bool
    assigned_count: int
    failed_count: int
    assignments: List[Dict[str, Any]]
    errors: List[str] = []