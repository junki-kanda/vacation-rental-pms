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
    CleaningDashboardStats, StaffPerformance,
    TaskAutoAssignRequest, TaskAutoAssignResponse,
    # Enums
    TaskStatus, ShiftStatus
)
from ..crud import cleaning as crud
from ..crud import staff_availability as availability_crud
from ..schemas.staff_availability import (
    StaffAvailability, StaffAvailabilityCreate, StaffAvailabilityUpdate
)

router = APIRouter(prefix="/api/cleaning", tags=["cleaning"])

# ========== スタッフ管理 ==========

@router.get("/staff", response_model=List[Staff])
def get_staff_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    facility_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """スタッフ一覧取得"""
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
        for shift in task.shifts:
            if shift.staff:
                assigned_staff.append({
                    "id": shift.staff.id,
                    "name": shift.staff.name,
                    "status": shift.status.value if hasattr(shift.status, 'value') else shift.status
                })
        
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
            "is_assigned": len(assigned_staff) > 0
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

@router.post("/tasks/auto-create")
def auto_create_tasks(
    checkout_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """チェックアウト日から清掃タスクを自動生成"""
    created_tasks = crud.auto_create_cleaning_tasks(db, checkout_date)
    return {
        "message": f"{len(created_tasks)} tasks created",
        "task_ids": [task.id for task in created_tasks]
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

@router.post("/tasks/auto-assign", response_model=TaskAutoAssignResponse)
def auto_assign_tasks(
    request: TaskAutoAssignRequest,
    db: Session = Depends(get_db)
):
    """タスク自動割当（簡易版）"""
    # TODO: 実装する自動割当アルゴリズム
    # 現在は簡易的な実装
    
    assigned_count = 0
    failed_count = 0
    assignments = []
    errors = []
    
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
        
        # 利用可能なスタッフを探す（簡易版）
        available_staff = crud.get_staff_list(db, is_active=True, facility_id=task.facility_id)
        
        if not available_staff:
            failed_count += 1
            errors.append(f"No available staff for task {task_id}")
            continue
        
        # 最初のスタッフに割り当て（簡易版）
        staff = available_staff[0]
        
        shift_create = CleaningShiftCreate(
            staff_id=staff.id,
            task_id=task.id,
            assigned_date=request.date,
            scheduled_start_time=task.scheduled_start_time or "10:00",
            scheduled_end_time=task.scheduled_end_time or "12:00",
            created_by="auto_assign"
        )
        
        try:
            shift = crud.create_cleaning_shift(db, shift_create)
            assigned_count += 1
            assignments.append({
                "task_id": task.id,
                "staff_id": staff.id,
                "staff_name": staff.name,
                "shift_id": shift.id
            })
        except Exception as e:
            failed_count += 1
            errors.append(f"Failed to assign task {task_id}: {str(e)}")
    
    return TaskAutoAssignResponse(
        success=assigned_count > 0,
        assigned_count=assigned_count,
        failed_count=failed_count,
        assignments=assignments,
        errors=errors
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