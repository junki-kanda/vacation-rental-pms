"""スタッフグループ管理機能のAPIエンドポイント"""
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import json

from ..database import get_db
from ..schemas.staff_group import (
    StaffGroup, StaffGroupCreate, StaffGroupUpdate,
    AddGroupMembers, RemoveGroupMembers,
    GroupAssignment
)
from ..crud import staff_group as crud

router = APIRouter(prefix="/api/staff-groups", tags=["staff-groups"])

# ========== スタッフグループ管理 ==========

@router.get("", response_model=List[StaffGroup])
def get_staff_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    facility_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """スタッフグループ一覧取得"""
    groups = crud.get_staff_groups(
        db, skip=skip, limit=limit,
        is_active=is_active, facility_id=facility_id
    )
    
    # メンバー情報を取得してstaff_nameを設定
    from ..models.cleaning import Staff as StaffModel
    for group in groups:
        for member in group.members:
            if member.left_date is None:
                staff = db.query(StaffModel).filter(StaffModel.id == member.staff_id).first()
                if staff:
                    member.staff_name = staff.name
        # メンバー数を計算
        active_members = [m for m in group.members if m.left_date is None]
        group.member_count = len(active_members)
    
    return groups

@router.get("/{group_id}", response_model=StaffGroup)
def get_staff_group(
    group_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """スタッフグループ詳細取得"""
    group = crud.get_staff_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Staff group not found")
    
    # メンバー情報を取得してstaff_nameを設定
    from ..models.cleaning import Staff as StaffModel
    for member in group.members:
        if member.left_date is None:
            staff = db.query(StaffModel).filter(StaffModel.id == member.staff_id).first()
            if staff:
                member.staff_name = staff.name
    
    # メンバー数を計算
    active_members = [m for m in group.members if m.left_date is None]
    group.member_count = len(active_members)
    
    return group

@router.post("", response_model=StaffGroup)
def create_staff_group(
    group: StaffGroupCreate,
    db: Session = Depends(get_db)
):
    """スタッフグループ作成"""
    return crud.create_staff_group(db, group)

@router.put("/{group_id}", response_model=StaffGroup)
def update_staff_group(
    group_id: int = Path(..., ge=1),
    group: StaffGroupUpdate = ...,
    db: Session = Depends(get_db)
):
    """スタッフグループ更新"""
    updated_group = crud.update_staff_group(db, group_id, group)
    if not updated_group:
        raise HTTPException(status_code=404, detail="Staff group not found")
    return updated_group

@router.delete("/{group_id}")
def delete_staff_group(
    group_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """スタッフグループ削除（論理削除）"""
    success = crud.delete_staff_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Staff group not found")
    return {"message": "Staff group deleted successfully"}

# ========== グループメンバー管理 ==========

@router.post("/{group_id}/members", response_model=StaffGroup)
def add_group_members(
    group_id: int = Path(..., ge=1),
    request: AddGroupMembers = ...,
    db: Session = Depends(get_db)
):
    """グループにメンバーを追加"""
    try:
        group = crud.add_group_members(db, group_id, request)
        # メンバー情報を取得してstaff_nameを設定
        from ..models.cleaning import Staff as StaffModel
        for member in group.members:
            if member.left_date is None:
                staff = db.query(StaffModel).filter(StaffModel.id == member.staff_id).first()
                if staff:
                    member.staff_name = staff.name
        # メンバー数を計算
        active_members = [m for m in group.members if m.left_date is None]
        group.member_count = len(active_members)
        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{group_id}/members", response_model=StaffGroup)
def remove_group_members(
    group_id: int = Path(..., ge=1),
    request: RemoveGroupMembers = ...,
    db: Session = Depends(get_db)
):
    """グループからメンバーを削除"""
    try:
        group = crud.remove_group_members(db, group_id, request)
        # メンバー情報を取得してstaff_nameを設定
        from ..models.cleaning import Staff as StaffModel
        for member in group.members:
            if member.left_date is None:
                staff = db.query(StaffModel).filter(StaffModel.id == member.staff_id).first()
                if staff:
                    member.staff_name = staff.name
        # メンバー数を計算
        active_members = [m for m in group.members if m.left_date is None]
        group.member_count = len(active_members)
        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ========== グループタスク割当 ==========

@router.post("/{group_id}/assign-tasks")
def assign_group_to_tasks(
    group_id: int = Path(..., ge=1),
    request: GroupAssignment = ...,
    db: Session = Depends(get_db)
):
    """グループをタスクに割り当て"""
    try:
        shifts = crud.assign_group_to_tasks(db, group_id, request)
        return {
            "success": True,
            "assigned_count": len(shifts),
            "shifts": [
                {
                    "shift_id": shift.id,
                    "task_id": shift.task_id,
                    "assigned_date": shift.assigned_date.isoformat(),
                    "scheduled_start_time": shift.scheduled_start_time.isoformat(),
                    "scheduled_end_time": shift.scheduled_end_time.isoformat()
                }
                for shift in shifts
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{group_id}/shifts")
def get_group_shifts(
    group_id: int = Path(..., ge=1),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """グループのシフト取得"""
    shifts = crud.get_group_shifts(db, group_id, start_date, end_date)
    return [
        {
            "shift_id": shift.id,
            "task_id": shift.task_id,
            "assigned_date": shift.assigned_date.isoformat(),
            "scheduled_start_time": shift.scheduled_start_time.isoformat(),
            "scheduled_end_time": shift.scheduled_end_time.isoformat(),
            "status": shift.status.value if shift.status else None,
            "task": {
                "facility_id": shift.task.facility_id,
                "checkout_date": shift.task.checkout_date.isoformat(),
                "status": shift.task.status.value if shift.task.status else None
            } if shift.task else None
        }
        for shift in shifts
    ]

@router.delete("/{group_id}/tasks/{task_id}")
def unassign_group_from_task(
    group_id: int = Path(..., ge=1),
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """グループのタスク割当解除"""
    success = crud.unassign_group_from_task(db, group_id, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Group unassigned from task successfully"}