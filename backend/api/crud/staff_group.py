"""スタッフグループ関連のCRUD操作"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, date

from ..models.cleaning import (
    StaffGroup as StaffGroupModel,
    StaffGroupMember as StaffGroupMemberModel,
    Staff as StaffModel,
    CleaningTask as CleaningTaskModel,
    CleaningShift as CleaningShiftModel,
    TaskStatus,
    ShiftStatus
)
from ..schemas.staff_group import (
    StaffGroupCreate, StaffGroupUpdate,
    AddGroupMembers, RemoveGroupMembers,
    GroupAssignment
)

# ========== スタッフグループCRUD ==========

def get_staff_group(db: Session, group_id: int) -> Optional[StaffGroupModel]:
    """スタッフグループ取得（メンバー情報含む）"""
    return db.query(StaffGroupModel)\
        .options(joinedload(StaffGroupModel.members).joinedload(StaffGroupMemberModel.staff))\
        .filter(StaffGroupModel.id == group_id).first()

def get_staff_groups(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    facility_id: Optional[int] = None
) -> List[StaffGroupModel]:
    """スタッフグループ一覧取得"""
    query = db.query(StaffGroupModel)\
        .options(joinedload(StaffGroupModel.members).joinedload(StaffGroupMemberModel.staff))
    
    if is_active is not None:
        query = query.filter(StaffGroupModel.is_active == is_active)
    
    if facility_id is not None:
        # JSONフィールドの検索
        query = query.filter(
            StaffGroupModel.available_facilities.contains([facility_id])
        )
    
    return query.offset(skip).limit(limit).all()

def create_staff_group(db: Session, group: StaffGroupCreate) -> StaffGroupModel:
    """スタッフグループ作成"""
    # グループ作成
    group_data = group.dict(exclude={'member_ids'})
    db_group = StaffGroupModel(**group_data)
    db.add(db_group)
    db.flush()  # IDを取得
    
    # 初期メンバー追加
    for staff_id in group.member_ids:
        member = StaffGroupMemberModel(
            group_id=db_group.id,
            staff_id=staff_id,
            role="メンバー",
            is_leader=False,
            joined_date=date.today()
        )
        db.add(member)
    
    db.commit()
    db.refresh(db_group)
    return db_group

def update_staff_group(
    db: Session,
    group_id: int,
    group: StaffGroupUpdate
) -> Optional[StaffGroupModel]:
    """スタッフグループ更新"""
    db_group = get_staff_group(db, group_id)
    if not db_group:
        return None
    
    update_data = group.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db_group.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_group)
    return db_group

def delete_staff_group(db: Session, group_id: int) -> bool:
    """スタッフグループ削除（論理削除）"""
    db_group = get_staff_group(db, group_id)
    if not db_group:
        return False
    
    db_group.is_active = False
    db_group.updated_at = datetime.utcnow()
    db.commit()
    return True

# ========== グループメンバー管理 ==========

def add_group_members(
    db: Session,
    group_id: int,
    request: AddGroupMembers
) -> StaffGroupModel:
    """グループにメンバーを追加"""
    group = get_staff_group(db, group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")
    
    # 既存メンバーのstaff_idを取得
    existing_member_ids = [m.staff_id for m in group.members if m.left_date is None]
    
    for staff_id in request.member_ids:
        if staff_id not in existing_member_ids:
            member = StaffGroupMemberModel(
                group_id=group_id,
                staff_id=staff_id,
                role=request.role or "メンバー",
                is_leader=request.is_leader,
                joined_date=date.today()
            )
            db.add(member)
    
    db.commit()
    db.refresh(group)
    return group

def remove_group_members(
    db: Session,
    group_id: int,
    request: RemoveGroupMembers
) -> StaffGroupModel:
    """グループからメンバーを削除（論理削除）"""
    group = get_staff_group(db, group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")
    
    # メンバーの脱退日を設定
    for member in group.members:
        if member.staff_id in request.member_ids and member.left_date is None:
            member.left_date = date.today()
            member.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(group)
    return group

def get_active_group_members(
    db: Session,
    group_id: int
) -> List[StaffModel]:
    """グループのアクティブメンバー取得"""
    members = db.query(StaffModel)\
        .join(StaffGroupMemberModel)\
        .filter(
            and_(
                StaffGroupMemberModel.group_id == group_id,
                StaffGroupMemberModel.left_date.is_(None)
            )
        ).all()
    
    return members

# ========== グループタスク割当 ==========

def assign_group_to_tasks(
    db: Session,
    group_id: int,
    request: GroupAssignment
) -> List[CleaningShiftModel]:
    """グループをタスクに割り当て"""
    group = get_staff_group(db, group_id)
    if not group:
        raise ValueError(f"Group {group_id} not found")
    
    created_shifts = []
    
    for task_id in request.task_ids:
        # タスクの存在確認
        task = db.query(CleaningTaskModel).filter(CleaningTaskModel.id == task_id).first()
        if not task:
            continue
        
        # 既存のシフトがないか確認
        existing_shift = db.query(CleaningShiftModel).filter(
            and_(
                CleaningShiftModel.task_id == task_id,
                or_(
                    CleaningShiftModel.group_id == group_id,
                    CleaningShiftModel.group_id.isnot(None)
                )
            )
        ).first()
        
        if existing_shift:
            continue  # 既に割当済み
        
        # グループシフト作成
        shift = CleaningShiftModel(
            group_id=group_id,
            staff_id=None,  # グループ割当なのでstaff_idはNULL
            task_id=task_id,
            assigned_date=request.assigned_date,
            scheduled_start_time=datetime.strptime(request.scheduled_start_time[:5], "%H:%M").time(),
            scheduled_end_time=datetime.strptime(request.scheduled_end_time[:5], "%H:%M").time(),
            status=ShiftStatus.SCHEDULED,
            # グループ報酬設定
            calculated_wage=group.rate_per_property,
            transportation_fee=group.transportation_fee,
            total_payment=group.rate_per_property + group.transportation_fee,
            notes=request.notes
        )
        
        db.add(shift)
        created_shifts.append(shift)
        
        # タスクのステータス更新
        task.status = TaskStatus.ASSIGNED
        task.updated_at = datetime.utcnow()
    
    if created_shifts:
        db.commit()
        for shift in created_shifts:
            db.refresh(shift)
    
    return created_shifts

def get_group_shifts(
    db: Session,
    group_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[CleaningShiftModel]:
    """グループのシフト取得"""
    query = db.query(CleaningShiftModel)\
        .options(joinedload(CleaningShiftModel.task))\
        .filter(CleaningShiftModel.group_id == group_id)
    
    if start_date:
        query = query.filter(CleaningShiftModel.assigned_date >= start_date)
    
    if end_date:
        query = query.filter(CleaningShiftModel.assigned_date <= end_date)
    
    return query.order_by(CleaningShiftModel.assigned_date).all()

def unassign_group_from_task(
    db: Session,
    group_id: int,
    task_id: int
) -> bool:
    """グループのタスク割当解除"""
    shift = db.query(CleaningShiftModel).filter(
        and_(
            CleaningShiftModel.group_id == group_id,
            CleaningShiftModel.task_id == task_id
        )
    ).first()
    
    if not shift:
        return False
    
    # シフト削除
    db.delete(shift)
    
    # タスクのステータスを未割当に戻す
    task = db.query(CleaningTaskModel).filter(CleaningTaskModel.id == task_id).first()
    if task:
        # 他のシフトがないか確認
        other_shifts = db.query(CleaningShiftModel).filter(
            CleaningShiftModel.task_id == task_id
        ).count()
        
        if other_shifts == 1:  # 削除前なので1
            task.status = TaskStatus.UNASSIGNED
            task.updated_at = datetime.utcnow()
    
    db.commit()
    return True