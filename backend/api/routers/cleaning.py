"""清掃管理機能のAPIエンドポイント"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from ..database import get_db
from ..schemas.cleaning import (
    # Staff
    Staff, StaffCreate, StaffUpdate,
    # CleaningTask
    CleaningTask, CleaningTaskCreate, CleaningTaskUpdate,
    # CleaningShift
    CleaningShift, CleaningShiftCreate, CleaningShiftUpdate,
    # FacilityCleaningSettings
    FacilityCleaningSettings, FacilityCleaningSettingsCreate, FacilityCleaningSettingsUpdate,
    # Dashboard
    CleaningDashboardStats, StaffPerformance, StaffMonthlyStats,
    TaskAutoAssignRequest, TaskAutoAssignResponse,
    # Enums
    TaskStatus, ShiftStatus
)
from ..crud import cleaning as crud
from ..crud import staff_availability as availability_crud
from ..schemas.staff_availability import (
    StaffAvailability, StaffAvailabilityCreate, StaffAvailabilityUpdate
)
from ..services.cleaning_sync import CleaningSyncService
from ..models.property import Facility

router = APIRouter(
    prefix="/api/cleaning",
    tags=["清掃管理"],
    responses={
        404: {"description": "Not found"},
        409: {"description": "Conflict"}
    }
)

# ========== スタッフ管理 ==========

@router.get(
    "/staff",
    response_model=List[Staff],
    summary="清掃スタッフ一覧の取得",
    description="登録されている清掃スタッフの一覧を取得します"
)
def get_staff_list(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=100, description="取得する最大件数"),
    is_active: Optional[bool] = Query(None, description="アクティブ状態でフィルター"),
    facility_id: Optional[int] = Query(None, description="対応可能施設IDでフィルター"),
    db: Session = Depends(get_db)
):
    """
    スタッフ一覧取得
    
    ### フィルター:
    - **is_active**: アクティブなスタッフのみ取得
    - **facility_id**: 特定の施設に対応可能なスタッフのみ取得
    """
    staff_list = crud.get_staff_list(
        db, skip=skip, limit=limit, 
        is_active=is_active, facility_id=facility_id
    )
    return staff_list

@router.get("/staff/{staff_id}", response_model=Staff)
def get_staff(
    staff_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """スタッフ詳細取得"""
    staff = crud.get_staff(db, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff

@router.post("/staff", response_model=Staff)
def create_staff(
    staff: StaffCreate,
    db: Session = Depends(get_db)
):
    """スタッフ作成"""
    # メールアドレスの重複チェック
    if staff.email:
        existing = crud.get_staff_by_email(db, staff.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_staff(db, staff)

@router.put("/staff/{staff_id}", response_model=Staff)
def update_staff(
    staff_id: int = Path(..., ge=1),
    staff: StaffUpdate = ...,
    db: Session = Depends(get_db)
):
    """スタッフ更新"""
    updated_staff = crud.update_staff(db, staff_id, staff)
    if not updated_staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return updated_staff

@router.delete("/staff/{staff_id}")
def delete_staff(
    staff_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """スタッフ削除（論理削除）"""
    success = crud.delete_staff(db, staff_id)
    if not success:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"message": "Staff deleted successfully"}

# ========== 清掃タスク管理 ==========

@router.get("/tasks", response_model=List[CleaningTask])
def get_cleaning_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    scheduled_date: Optional[date] = None,
    status: Optional[TaskStatus] = None,
    facility_id: Optional[int] = None,
    unassigned_only: bool = False,
    db: Session = Depends(get_db)
):
    """清掃タスク一覧取得"""
    tasks = crud.get_cleaning_tasks(
        db, skip=skip, limit=limit,
        scheduled_date=scheduled_date,
        status=status,
        facility_id=facility_id,
        unassigned_only=unassigned_only
    )
    
    # リレーション情報を追加
    for task in tasks:
        if task.facility:
            task.facility_name = task.facility.name
        if task.reservation:
            task.guest_name = task.reservation.guest_name
    
    return tasks

@router.get("/tasks/calendar", response_model=dict)
def get_tasks_for_calendar(
    start_date: date = Query(...),
    end_date: date = Query(...),
    facility_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """カレンダー表示用の清掃タスクデータ取得"""
    # タスクを期間内で取得
    tasks = crud.get_cleaning_tasks_by_date_range(
        db, 
        start_date=start_date, 
        end_date=end_date,
        facility_id=facility_id
    )
    
    # 施設情報も取得
    from ..models.property import Facility
    facilities = db.query(Facility).all()
    
    # タスクを日付と施設でグループ化
    tasks_by_date = {}
    for task in tasks:
        date_str = str(task.scheduled_date)
        if date_str not in tasks_by_date:
            tasks_by_date[date_str] = []
        
        # シフト情報も含める
        assigned_staff = []
        assigned_group = None
        is_assigned = False
        
        for shift in task.shifts:
            if shift.staff:
                # 個人割当の場合
                assigned_staff.append({
                    "id": shift.staff.id,
                    "name": shift.staff.name,
                    "status": shift.status.value if hasattr(shift.status, 'value') else shift.status
                })
                is_assigned = True
            elif shift.group:
                # グループ割当の場合
                assigned_group = {
                    "id": shift.group.id,
                    "name": shift.group.name,
                    "member_count": len([m for m in shift.group.members if m.left_date is None])
                }
                is_assigned = True
        
        tasks_by_date[date_str].append({
            "id": task.id,
            "facility_id": task.facility_id,
            "facility_name": task.facility.name if task.facility else f"施設{task.facility_id}",
            "checkout_date": str(task.checkout_date),
            "scheduled_date": str(task.scheduled_date),
            "scheduled_start_time": str(task.scheduled_start_time) if task.scheduled_start_time else None,
            "scheduled_end_time": str(task.scheduled_end_time) if task.scheduled_end_time else None,
            "status": task.status.value if hasattr(task.status, 'value') else task.status,
            "guest_name": task.reservation.guest_name if task.reservation else None,
            "assigned_staff": assigned_staff,
            "assigned_group": assigned_group,
            "is_assigned": is_assigned
        })
    
    return {
        "tasks_by_date": tasks_by_date,
        "facilities": [{"id": f.id, "name": f.name} for f in facilities]
    }

@router.get("/tasks/{task_id}", response_model=CleaningTask)
def get_cleaning_task(
    task_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """清掃タスク詳細取得"""
    task = crud.get_cleaning_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.facility:
        task.facility_name = task.facility.name
    if task.reservation:
        task.guest_name = task.reservation.guest_name
    
    return task

@router.post("/tasks", response_model=CleaningTask)
def create_cleaning_task(
    task: CleaningTaskCreate,
    db: Session = Depends(get_db)
):
    """清掃タスク作成"""
    return crud.create_cleaning_task(db, task)

@router.put("/tasks/{task_id}", response_model=CleaningTask)
def update_cleaning_task(
    task_id: int = Path(..., ge=1),
    task: CleaningTaskUpdate = ...,
    db: Session = Depends(get_db)
):
    """清掃タスク更新"""
    updated_task = crud.update_cleaning_task(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

@router.patch("/tasks/{task_id}/status")
def update_task_status(
    task_id: int = Path(..., ge=1),
    status: str = Query(...),
    db: Session = Depends(get_db)
):
    """タスクステータス更新"""
    from ..models.cleaning import TaskStatus
    
    # ステータスの妥当性チェック
    valid_statuses = [status.value for status in TaskStatus]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid options: {valid_statuses}")
    
    task = crud.get_cleaning_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # ステータス更新
    from ..schemas.cleaning import CleaningTaskUpdate
    task_update = CleaningTaskUpdate(status=status)
    updated_task = crud.update_cleaning_task(db, task_id, task_update)
    
    # needs_revision ステータスの場合、特別な処理を実行
    if status == TaskStatus.NEEDS_REVISION.value:
        # タスクが割り当て済みの場合、一旦未割当に戻す
        if task.status == TaskStatus.ASSIGNED.value:
            from ..crud.cleaning import unassign_task_from_staff
            unassign_task_from_staff(db, task_id)
    
    return {"message": f"Task status updated to {status}", "task_id": task_id, "new_status": status}

@router.post("/tasks/{task_id}/revision")
def request_task_revision(
    task_id: int = Path(..., ge=1),
    revision_reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """タスクの修正要求"""
    task = crud.get_cleaning_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # タスクを要修正状態に変更
    from ..schemas.cleaning import CleaningTaskUpdate
    task_update = CleaningTaskUpdate(
        status=TaskStatus.NEEDS_REVISION.value,
        special_instructions=f"{task.special_instructions or ''}\n【修正要求】{revision_reason}" if task.special_instructions else f"【修正要求】{revision_reason}"
    )
    updated_task = crud.update_cleaning_task(db, task_id, task_update)
    
    # 割り当てられたスタッフ/グループがいる場合は解除
    from ..crud.cleaning import unassign_task_from_staff
    unassign_task_from_staff(db, task_id)
    
    return {
        "message": "Task marked for revision",
        "task_id": task_id,
        "revision_reason": revision_reason
    }

@router.get("/tasks/needs-revision")
def get_tasks_needing_revision(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    facility_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """要修正タスク一覧取得"""
    query = db.query(CleaningTask).filter(CleaningTask.status == TaskStatus.NEEDS_REVISION)
    
    if facility_id:
        query = query.filter(CleaningTask.facility_id == facility_id)
    
    tasks = query.offset(skip).limit(limit).all()
    
    # 施設情報を付与
    for task in tasks:
        if task.facility:
            task.facility_name = task.facility.name
    
    return tasks

@router.post("/tasks/{task_id}/resolve-revision")
def resolve_task_revision(
    task_id: int = Path(..., ge=1),
    resolution_notes: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """タスクの修正対応完了"""
    task = crud.get_cleaning_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.NEEDS_REVISION.value:
        raise HTTPException(status_code=400, detail="Task is not in needs_revision status")
    
    # タスクを未割当状態に戻す
    from ..schemas.cleaning import CleaningTaskUpdate
    task_update = CleaningTaskUpdate(
        status=TaskStatus.UNASSIGNED.value,
        special_instructions=f"{task.special_instructions or ''}\n【修正対応完了】{resolution_notes}" if task.special_instructions else f"【修正対応完了】{resolution_notes}"
    )
    updated_task = crud.update_cleaning_task(db, task_id, task_update)
    
    return {
        "message": "Task revision resolved",
        "task_id": task_id,
        "resolution_notes": resolution_notes
    }

@router.post("/tasks/auto-create")
def auto_create_tasks(
    checkout_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """チェックアウト日から清掃タスクを自動生成"""
    result = crud.auto_create_cleaning_tasks(db, checkout_date)
    return {
        "message": f"{result.stats['created_tasks']} tasks created, {result.stats['errors']} errors",
        "task_ids": [task.id for task in result.created_tasks],
        "stats": result.stats,
        "errors": result.errors,
        "warnings": result.warnings
    }

# ========== シフト管理 ==========

@router.get("/shifts", response_model=List[CleaningShift])
def get_cleaning_shifts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    assigned_date: Optional[date] = None,
    staff_id: Optional[int] = None,
    status: Optional[ShiftStatus] = None,
    db: Session = Depends(get_db)
):
    """シフト一覧取得"""
    shifts = crud.get_cleaning_shifts(
        db, skip=skip, limit=limit,
        assigned_date=assigned_date,
        staff_id=staff_id,
        status=status
    )
    
    # リレーション情報を追加
    for shift in shifts:
        if shift.staff:
            shift.staff_name = shift.staff.name
        if shift.task and shift.task.facility:
            shift.facility_name = shift.task.facility.name
    
    return shifts

@router.get("/shifts/{shift_id}", response_model=CleaningShift)
def get_cleaning_shift(
    shift_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """シフト詳細取得"""
    shift = crud.get_cleaning_shift(db, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    if shift.staff:
        shift.staff_name = shift.staff.name
    if shift.task and shift.task.facility:
        shift.facility_name = shift.task.facility.name
    
    return shift

@router.post("/shifts", response_model=CleaningShift)
def create_cleaning_shift(
    shift: CleaningShiftCreate,
    db: Session = Depends(get_db)
):
    """シフト作成（スタッフをタスクに割当）"""
    # スタッフとタスクの存在確認
    staff = crud.get_staff(db, shift.staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    task = crud.get_cleaning_task(db, shift.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 既存のシフトがないか確認
    existing_shifts = crud.get_cleaning_shifts(db, staff_id=shift.staff_id, assigned_date=shift.assigned_date)
    for existing in existing_shifts:
        if existing.task_id == shift.task_id:
            raise HTTPException(status_code=400, detail="Shift already exists for this task and staff")
    
    return crud.create_cleaning_shift(db, shift)

@router.put("/shifts/{shift_id}", response_model=CleaningShift)
def update_cleaning_shift(
    shift_id: int = Path(..., ge=1),
    shift: CleaningShiftUpdate = ...,
    db: Session = Depends(get_db)
):
    """シフト更新"""
    updated_shift = crud.update_cleaning_shift(db, shift_id, shift)
    if not updated_shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return updated_shift

@router.delete("/shifts/{shift_id}")
def delete_cleaning_shift(
    shift_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """シフト削除"""
    success = crud.delete_cleaning_shift(db, shift_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shift not found")
    return {"message": "Shift deleted successfully"}

@router.post("/shifts/{shift_id}/check-in")
def check_in_shift(
    shift_id: int = Path(..., ge=1),
    location: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """シフトチェックイン（作業開始）"""
    shift_update = CleaningShiftUpdate(
        status=ShiftStatus.IN_PROGRESS,
        actual_start_time=datetime.utcnow(),
        check_in_location=location
    )
    updated_shift = crud.update_cleaning_shift(db, shift_id, shift_update)
    if not updated_shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return {"message": "Checked in successfully", "shift_id": shift_id}

@router.post("/shifts/{shift_id}/check-out")
def check_out_shift(
    shift_id: int = Path(..., ge=1),
    location: Optional[dict] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """シフトチェックアウト（作業完了）"""
    shift_update = CleaningShiftUpdate(
        status=ShiftStatus.COMPLETED,
        actual_end_time=datetime.utcnow(),
        check_out_location=location,
        notes=notes
    )
    updated_shift = crud.update_cleaning_shift(db, shift_id, shift_update)
    if not updated_shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return {"message": "Checked out successfully", "shift_id": shift_id}

# ========== 施設清掃設定 ==========

@router.get("/facilities/{facility_id}/settings", response_model=FacilityCleaningSettings)
def get_facility_settings(
    facility_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """施設清掃設定取得"""
    settings = crud.get_facility_cleaning_settings(db, facility_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@router.post("/facilities/{facility_id}/settings", response_model=FacilityCleaningSettings)
def create_facility_settings(
    facility_id: int = Path(..., ge=1),
    settings: FacilityCleaningSettingsCreate = ...,
    db: Session = Depends(get_db)
):
    """施設清掃設定作成"""
    # 既存設定がないか確認
    existing = crud.get_facility_cleaning_settings(db, facility_id)
    if existing:
        raise HTTPException(status_code=400, detail="Settings already exist for this facility")
    
    settings.facility_id = facility_id
    return crud.create_facility_cleaning_settings(db, settings)

@router.put("/facilities/{facility_id}/settings", response_model=FacilityCleaningSettings)
def update_facility_settings(
    facility_id: int = Path(..., ge=1),
    settings: FacilityCleaningSettingsUpdate = ...,
    db: Session = Depends(get_db)
):
    """施設清掃設定更新"""
    updated_settings = crud.update_facility_cleaning_settings(db, facility_id, settings)
    if not updated_settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return updated_settings

# ========== ダッシュボード ==========

@router.get("/dashboard/stats", response_model=CleaningDashboardStats)
def get_dashboard_stats(
    target_date: date = Query(default=date.today()),
    db: Session = Depends(get_db)
):
    """清掃ダッシュボード統計取得"""
    stats = crud.get_cleaning_dashboard_stats(db, target_date)
    return CleaningDashboardStats(**stats)

@router.get("/dashboard/staff-performance", response_model=List[StaffPerformance])
def get_staff_performance(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """スタッフパフォーマンス取得"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Invalid date range")
    
    performance = crud.get_staff_performance(db, start_date, end_date)
    return [StaffPerformance(**p) for p in performance]

@router.get("/dashboard/staff-monthly-stats", response_model=List[StaffMonthlyStats])
def get_staff_monthly_stats(
    year: int = Query(..., ge=2020, le=2030),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db)
):
    """スタッフ月次統計取得
    
    指定月のスタッフごとの出勤日数、担当棟数を集計
    """
    from ..models.cleaning import Staff as StaffModel, CleaningShift as ShiftModel, StaffGroupMember, CleaningTask as TaskModel
    from sqlalchemy import func, and_, extract
    from datetime import datetime, date
    import calendar
    
    # 月の開始日と終了日を計算
    _, last_day = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)
    
    # アクティブなスタッフを取得
    staff_list = db.query(StaffModel).filter(StaffModel.is_active == True).all()
    
    stats = []
    for staff in staff_list:
        # 個人割当のシフトを取得
        individual_shifts = db.query(ShiftModel).filter(
            and_(
                ShiftModel.staff_id == staff.id,
                ShiftModel.assigned_date >= start_date,
                ShiftModel.assigned_date <= end_date,
                ShiftModel.status != "cancelled"
            )
        ).all()
        
        # グループ割当のシフトを取得（スタッフが所属するグループ経由）
        group_shifts = db.query(ShiftModel).join(
            StaffGroupMember,
            and_(
                ShiftModel.group_id == StaffGroupMember.group_id,
                StaffGroupMember.staff_id == staff.id,
                StaffGroupMember.left_date.is_(None)
            )
        ).filter(
            and_(
                ShiftModel.assigned_date >= start_date,
                ShiftModel.assigned_date <= end_date,
                ShiftModel.status != "cancelled"
            )
        ).all()
        
        # 出勤日を集計
        dates_worked = set()
        individual_task_count = 0
        group_task_count = 0
        total_hours = 0.0
        
        for shift in individual_shifts:
            dates_worked.add(shift.assigned_date)
            individual_task_count += 1
            # タスクから推定時間を取得
            task = db.query(TaskModel).filter(TaskModel.id == shift.task_id).first()
            if task:
                total_hours += (task.estimated_duration_minutes or 300) / 60.0
        
        for shift in group_shifts:
            dates_worked.add(shift.assigned_date)
            group_task_count += 1
            # グループタスクの場合は時間を按分
            task = db.query(TaskModel).filter(TaskModel.id == shift.task_id).first()
            if task:
                # グループメンバー数で按分
                group_member_count = db.query(func.count(StaffGroupMember.id)).filter(
                    and_(
                        StaffGroupMember.group_id == shift.group_id,
                        StaffGroupMember.left_date.is_(None)
                    )
                ).scalar() or 1
                total_hours += ((task.estimated_duration_minutes or 300) / 60.0) / group_member_count
        
        stats.append(StaffMonthlyStats(
            staff_id=staff.id,
            staff_name=staff.name,
            year=year,
            month=month,
            working_days=len(dates_worked),
            total_tasks=individual_task_count + group_task_count,
            individual_tasks=individual_task_count,
            group_tasks=group_task_count,
            total_hours=round(total_hours, 1),
            dates_worked=sorted(list(dates_worked))
        ))
    
    # 出勤日数でソート（降順）
    stats.sort(key=lambda x: x.working_days, reverse=True)
    
    return stats

@router.post("/tasks/sync-all")
def sync_all_cleaning_tasks(
    db: Session = Depends(get_db)
):
    """全清掃タスクを最新の予約データと同期
    
    新規予約の追加、キャンセル検知、変更検知を行い、
    割当済みタスクへの影響がある場合はアラートを生成する
    """
    sync_service = CleaningSyncService(db)
    result = sync_service.sync_all_tasks()
    return result

@router.get("/tasks/sync-preview")
def preview_sync_cleaning_tasks(
    db: Session = Depends(get_db)
):
    """同期のプレビュー（実際の変更は行わない）"""
    sync_service = CleaningSyncService(db)
    result = sync_service.get_sync_preview()
    return result

@router.post("/tasks/auto-assign", response_model=TaskAutoAssignResponse)
def auto_assign_tasks(
    request: TaskAutoAssignRequest,
    db: Session = Depends(get_db)
):
    """タスク自動割当（高度なアルゴリズム）
    
    割当優先順位:
    1. スタッフの出勤可能日を確認
    2. 既存シフト数が少ないスタッフを優先（負荷分散）
    3. 施設への適合性を考慮
    4. グループ割当の場合はグループメンバーを優先
    5. タスクの優先度と締切を考慮
    """
    from ..crud import staff_availability as availability_crud
    from ..crud import staff_group as group_crud
    from collections import defaultdict
    
    assigned_count = 0
    failed_count = 0
    assignments = []
    errors = []
    
    # タスクを優先度でソート（高優先度、締切が近いものから）
    task_ids_sorted = []
    task_details = {}
    
    for task_id in request.task_ids:
        task = crud.get_cleaning_task(db, task_id)
        if not task:
            failed_count += 1
            errors.append(f"Task {task_id} not found")
            continue
        
        if task.status != TaskStatus.UNASSIGNED:
            failed_count += 1
            errors.append(f"Task {task_id} is already assigned")
            continue
        
        # タスクの詳細を保存
        # priority は整数 (1-5、1が最高優先度)
        priority_score = 0
        if task.priority:
            priority_score = (6 - task.priority) * 20  # 1->100, 2->80, 3->60, 4->40, 5->20
        else:
            priority_score = 60  # デフォルトは中程度
        
        # checkout_dateまでの日数を考慮（deadlineフィールドは存在しない）
        if task.checkout_date and request.date:
            days_until_checkout = (task.checkout_date - request.date).days
            priority_score += max(0, 10 - days_until_checkout)  # チェックアウトが近いほど高スコア
        
        task_details[task_id] = {
            "task": task,
            "priority_score": priority_score
        }
        task_ids_sorted.append((task_id, priority_score))
    
    # 優先度でソート
    task_ids_sorted.sort(key=lambda x: x[1], reverse=True)
    
    # スタッフごとの既存シフト数をカウント
    staff_shift_counts = defaultdict(int)
    existing_shifts = crud.get_cleaning_shifts(
        db, 
        assigned_date=request.date,
        limit=1000
    )
    for shift in existing_shifts:
        staff_shift_counts[shift.staff_id] += 1
    
    # 各タスクに対して最適なスタッフを割り当て
    for task_id, _ in task_ids_sorted:
        task = task_details[task_id]["task"]
        
        # 利用可能なスタッフを取得
        all_staff = crud.get_staff_list(db, is_active=True)
        
        # スタッフをスコアリング
        staff_scores = []
        
        for staff in all_staff:
            score = 0
            reasons = []
            
            # 1. 出勤可能日チェック
            if request.date:
                availability = availability_crud.get_staff_availability(
                    db,
                    staff.id,
                    request.date.year,
                    request.date.month
                )
                
                if availability:
                    day_column = f"day_{request.date.day}"
                    if hasattr(availability, day_column):
                        is_available = getattr(availability, day_column)
                        if not is_available:
                            continue  # このスタッフは出勤不可
                        else:
                            score += 20
                            reasons.append("available")
            
            # 2. 既存シフト数（負荷分散）
            current_shifts = staff_shift_counts.get(staff.id, 0)
            if current_shifts == 0:
                score += 30
                reasons.append("no_shifts")
            elif current_shifts < 3:
                score += 20
                reasons.append("few_shifts")
            elif current_shifts < 5:
                score += 10
                reasons.append("moderate_shifts")
            else:
                score += 0  # 既に多くのシフトがある
                reasons.append("many_shifts")
            
            # 3. 施設への適合性
            if staff.available_facilities:
                if task.facility_id in staff.available_facilities:
                    score += 25
                    reasons.append("facility_match")
                else:
                    # 施設が合わない場合はスキップ
                    continue
            else:
                # 施設指定がない場合は全施設対応可能とみなす
                score += 15
                reasons.append("all_facilities")
            
            # 4. グループ割当の考慮
            if hasattr(task, 'assigned_group_id') and task.assigned_group_id:
                # グループメンバーかチェック
                members = group_crud.get_group_members(db, task.assigned_group_id)
                member_ids = [m.staff_id for m in members if not m.left_date]
                if staff.id in member_ids:
                    score += 40  # グループメンバーを強く優先
                    reasons.append("group_member")
                else:
                    # グループ専用タスクの場合、メンバー以外は除外
                    continue
            
            # 5. 大型施設対応能力（max_guests > 6 を大型施設とみなす）
            if task.facility_id:
                facility = db.query(Facility).filter(Facility.id == task.facility_id).first()
                if facility and facility.max_guests and facility.max_guests > 6:
                    if getattr(staff, 'can_handle_large_properties', False):
                        score += 15
                        reasons.append("large_property_capable")
                    else:
                        score -= 10
                        reasons.append("not_large_capable")
            
            # 6. スキルレベル（将来的な拡張用）
            if hasattr(staff, 'skill_level'):
                if staff.skill_level == "expert":
                    score += 10
                    reasons.append("expert")
                elif staff.skill_level == "intermediate":
                    score += 5
                    reasons.append("intermediate")
            
            staff_scores.append({
                "staff": staff,
                "score": score,
                "reasons": reasons
            })
        
        # スコアでソート（高い順）
        staff_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # 最適なスタッフを選択
        if not staff_scores:
            failed_count += 1
            errors.append(f"No available staff for task {task_id}")
            continue
        
        best_staff = staff_scores[0]["staff"]
        best_score = staff_scores[0]["score"]
        assignment_reasons = staff_scores[0]["reasons"]
        
        # シフトを作成
        shift_create = CleaningShiftCreate(
            staff_id=best_staff.id,
            task_id=task.id,
            assigned_date=request.date,
            scheduled_start_time=task.scheduled_start_time or "11:00",
            scheduled_end_time=task.scheduled_end_time or "16:00",
            created_by="auto_assign"
        )
        
        try:
            shift = crud.create_cleaning_shift(db, shift_create)
            assigned_count += 1
            
            # このスタッフのシフト数を更新
            staff_shift_counts[best_staff.id] += 1
            
            assignments.append({
                "task_id": task.id,
                "staff_id": best_staff.id,
                "staff_name": best_staff.name,
                "shift_id": shift.id,
                "score": best_score,
                "reasons": assignment_reasons
            })
        except Exception as e:
            failed_count += 1
            errors.append(f"Failed to assign task {task_id}: {str(e)}")
    
    return TaskAutoAssignResponse(
        success=assigned_count > 0,
        assigned_count=assigned_count,
        failed_count=failed_count,
        assignments=assignments,
        errors=errors,
        message=f"自動割当完了: {assigned_count}件成功, {failed_count}件失敗"
    )

# ========== スタッフ出勤可能日管理 ==========

@router.get("/staff/{staff_id}/availability/{year}/{month}", response_model=dict)
def get_staff_availability(
    staff_id: int = Path(..., ge=1),
    year: int = Path(..., ge=2020, le=2100),
    month: int = Path(..., ge=1, le=12),
    db: Session = Depends(get_db)
):
    """スタッフの月別出勤可能日を取得"""
    availability = availability_crud.get_staff_availability(db, staff_id, year, month)
    
    if not availability:
        # 初期化して返す
        availability = availability_crud.initialize_month_availability(
            db, staff_id, year, month, default_available=True
        )
    
    return availability_crud.convert_model_to_dict(availability)

@router.post("/staff/{staff_id}/availability", response_model=dict)
def create_or_update_availability(
    staff_id: int = Path(..., ge=1),
    availability: StaffAvailabilityCreate = ...,
    db: Session = Depends(get_db)
):
    """スタッフの出勤可能日を作成または更新"""
    # staff_idをパスパラメータから設定
    availability.staff_id = staff_id
    
    result = availability_crud.create_or_update_staff_availability(db, availability)
    return availability_crud.convert_model_to_dict(result)

@router.put("/staff/{staff_id}/availability/{year}/{month}", response_model=dict)
def update_availability(
    staff_id: int = Path(..., ge=1),
    year: int = Path(..., ge=2020, le=2100),
    month: int = Path(..., ge=1, le=12),
    update_data: StaffAvailabilityUpdate = ...,
    db: Session = Depends(get_db)
):
    """特定月の出勤可能日を更新"""
    updated = availability_crud.update_staff_availability(
        db, staff_id, year, month, update_data
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Availability record not found")
    
    return availability_crud.convert_model_to_dict(updated)

@router.get("/availability/{year}/{month}", response_model=List[dict])
def get_monthly_availability(
    year: int = Path(..., ge=2020, le=2100),
    month: int = Path(..., ge=1, le=12),
    db: Session = Depends(get_db)
):
    """特定月の全スタッフの出勤可能日を取得"""
    availabilities = availability_crud.get_staff_availabilities_by_month(db, year, month)
    return [availability_crud.convert_model_to_dict(a) for a in availabilities]

@router.get("/availability/{year}/{month}/{day}/staff", response_model=List[int])
def get_available_staff_for_date(
    year: int = Path(..., ge=2020, le=2100),
    month: int = Path(..., ge=1, le=12),
    day: int = Path(..., ge=1, le=31),
    db: Session = Depends(get_db)
):
    """特定日に出勤可能なスタッフIDリストを取得"""
    staff_ids = availability_crud.get_available_staff_for_date(db, year, month, day)
    return staff_ids