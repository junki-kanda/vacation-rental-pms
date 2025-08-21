"""スタッフグループ関連のスキーマ定義"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

# ========== StaffGroupMember ==========

class StaffGroupMemberBase(BaseModel):
    """グループメンバー基本スキーマ"""
    staff_id: int
    role: Optional[str] = None
    is_leader: bool = False

class StaffGroupMemberCreate(StaffGroupMemberBase):
    """グループメンバー作成スキーマ"""
    pass

class StaffGroupMemberUpdate(BaseModel):
    """グループメンバー更新スキーマ"""
    role: Optional[str] = None
    is_leader: Optional[bool] = None
    left_date: Optional[date] = None

class StaffGroupMemberInDB(StaffGroupMemberBase):
    """グループメンバーDB格納スキーマ"""
    id: int
    group_id: int
    joined_date: date
    left_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    # リレーション
    staff_name: Optional[str] = None  # スタッフ名（JOINして取得）
    
    class Config:
        orm_mode = True

class StaffGroupMember(StaffGroupMemberInDB):
    """グループメンバー出力スキーマ"""
    pass

# ========== StaffGroup ==========

class StaffGroupBase(BaseModel):
    """スタッフグループ基本スキーマ"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    can_handle_large_properties: bool = True
    can_handle_multiple_properties: bool = True
    max_properties_per_day: int = Field(default=1, ge=1, le=10)
    available_facilities: List[int] = []
    rate_per_property: float = Field(default=8000, ge=0)
    rate_per_property_with_option: float = Field(default=9000, ge=0)
    transportation_fee: float = Field(default=0, ge=0)
    is_active: bool = True
    notes: Optional[str] = None

class StaffGroupCreate(StaffGroupBase):
    """スタッフグループ作成スキーマ"""
    member_ids: List[int] = []  # 初期メンバーのID

class StaffGroupUpdate(BaseModel):
    """スタッフグループ更新スキーマ"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    can_handle_large_properties: Optional[bool] = None
    can_handle_multiple_properties: Optional[bool] = None
    max_properties_per_day: Optional[int] = Field(None, ge=1, le=10)
    available_facilities: Optional[List[int]] = None
    rate_per_property: Optional[float] = Field(None, ge=0)
    rate_per_property_with_option: Optional[float] = Field(None, ge=0)
    transportation_fee: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class StaffGroupInDB(StaffGroupBase):
    """スタッフグループDB格納スキーマ"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class StaffGroup(StaffGroupInDB):
    """スタッフグループ出力スキーマ"""
    members: List[StaffGroupMember] = []
    member_count: int = 0
    
    class Config:
        orm_mode = True

# ========== グループ管理用スキーマ ==========

class AddGroupMembers(BaseModel):
    """グループメンバー追加スキーマ"""
    member_ids: List[int]
    role: Optional[str] = None
    is_leader: bool = False

class RemoveGroupMembers(BaseModel):
    """グループメンバー削除スキーマ"""
    member_ids: List[int]

class GroupAssignment(BaseModel):
    """グループタスク割当スキーマ"""
    task_ids: List[int]
    assigned_date: date
    scheduled_start_time: str = "11:00"
    scheduled_end_time: str = "16:00"
    notes: Optional[str] = None