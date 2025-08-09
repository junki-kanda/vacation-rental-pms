"""清掃管理機能のCRUD操作"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time, timedelta

from ..models.cleaning import (
    Staff as StaffModel,
    CleaningTask as CleaningTaskModel,
    CleaningShift as CleaningShiftModel,
    FacilityCleaningSettings as FacilityCleaningSettingsModel,
    TaskStatus,
    ShiftStatus
)
from ..models.reservation import Reservation
from ..models.property import Facility
from ..schemas.cleaning import (
    StaffCreate, StaffUpdate,
    CleaningTaskCreate, CleaningTaskUpdate,
    CleaningShiftCreate, CleaningShiftUpdate,
    FacilityCleaningSettingsCreate, FacilityCleaningSettingsUpdate
)

# ========== スタッフ関連 ==========

def get_staff(db: Session, staff_id: int) -> Optional[StaffModel]:
    """スタッフ取得"""
    return db.query(StaffModel).filter(StaffModel.id == staff_id).first()

def get_staff_by_email(db: Session, email: str) -> Optional[StaffModel]:
    """メールアドレスでスタッフ取得"""
    return db.query(StaffModel).filter(StaffModel.email == email).first()

def get_staff_list(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    facility_id: Optional[int] = None
) -> List[StaffModel]:
    """スタッフ一覧取得"""
    query = db.query(StaffModel)
    
    if is_active is not None:
        query = query.filter(StaffModel.is_active == is_active)
    
    if facility_id is not None:
        # JSONフィールドの検索（SQLiteの場合）
        query = query.filter(
            func.json_extract(StaffModel.available_facilities, f'$[*]').like(f'%{facility_id}%')
        )
    
    return query.offset(skip).limit(limit).all()

def get_cleaning_tasks_by_date_range(
    db: Session,
    start_date: date,
    end_date: date,
    facility_id: Optional[int] = None
) -> List[CleaningTaskModel]:
    """日付範囲で清掃タスクを取得（カレンダー用）"""
    query = db.query(CleaningTaskModel)\
        .options(joinedload(CleaningTaskModel.facility))\
        .options(joinedload(CleaningTaskModel.reservation))\
        .options(joinedload(CleaningTaskModel.shifts).joinedload(CleaningShiftModel.staff))
    
    # 日付フィルタ
    query = query.filter(
        and_(
            CleaningTaskModel.scheduled_date >= start_date,
            CleaningTaskModel.scheduled_date <= end_date
        )
    )
    
    # 施設フィルタ
    if facility_id:
        query = query.filter(CleaningTaskModel.facility_id == facility_id)
    
    return query.order_by(CleaningTaskModel.scheduled_date, CleaningTaskModel.scheduled_start_time).all()

def create_staff(db: Session, staff: StaffCreate) -> StaffModel:
    """スタッフ作成"""
    staff_data = staff.dict()
    # 空文字列のemailはNoneに変換（UNIQUE制約対策）
    if 'email' in staff_data and not staff_data['email']:
        staff_data['email'] = None
    
    db_staff = StaffModel(**staff_data)
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

def update_staff(db: Session, staff_id: int, staff: StaffUpdate) -> Optional[StaffModel]:
    """スタッフ更新"""
    db_staff = get_staff(db, staff_id)
    if not db_staff:
        return None
    
    update_data = staff.dict(exclude_unset=True)
    # 空文字列のemailはNoneに変換（UNIQUE制約対策）
    if 'email' in update_data and not update_data['email']:
        update_data['email'] = None
    
    for field, value in update_data.items():
        setattr(db_staff, field, value)
    
    db_staff.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_staff)
    return db_staff

def delete_staff(db: Session, staff_id: int) -> bool:
    """スタッフ削除（論理削除）"""
    db_staff = get_staff(db, staff_id)
    if not db_staff:
        return False
    
    db_staff.is_active = False
    db_staff.updated_at = datetime.utcnow()
    db.commit()
    return True

# ========== 清掃タスク関連 ==========

def get_cleaning_task(db: Session, task_id: int) -> Optional[CleaningTaskModel]:
    """清掃タスク取得"""
    return db.query(CleaningTaskModel)\
        .options(joinedload(CleaningTaskModel.facility))\
        .options(joinedload(CleaningTaskModel.reservation))\
        .filter(CleaningTaskModel.id == task_id).first()

def get_cleaning_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    scheduled_date: Optional[date] = None,
    status: Optional[TaskStatus] = None,
    facility_id: Optional[int] = None,
    unassigned_only: bool = False
) -> List[CleaningTaskModel]:
    """清掃タスク一覧取得"""
    query = db.query(CleaningTaskModel)\
        .options(joinedload(CleaningTaskModel.facility))\
        .options(joinedload(CleaningTaskModel.reservation))
    
    if scheduled_date:
        query = query.filter(CleaningTaskModel.scheduled_date == scheduled_date)
    
    if status:
        query = query.filter(CleaningTaskModel.status == status)
    
    if facility_id:
        query = query.filter(CleaningTaskModel.facility_id == facility_id)
    
    if unassigned_only:
        query = query.filter(CleaningTaskModel.status == TaskStatus.UNASSIGNED)
    
    return query.order_by(CleaningTaskModel.scheduled_date, CleaningTaskModel.priority)\
        .offset(skip).limit(limit).all()

def create_cleaning_task(db: Session, task: CleaningTaskCreate) -> CleaningTaskModel:
    """清掃タスク作成"""
    db_task = CleaningTaskModel(**task.dict())
    db_task.status = TaskStatus.UNASSIGNED
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_cleaning_task(
    db: Session,
    task_id: int,
    task: CleaningTaskUpdate
) -> Optional[CleaningTaskModel]:
    """清掃タスク更新"""
    db_task = get_cleaning_task(db, task_id)
    if not db_task:
        return None
    
    update_data = task.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # 実績時間の自動計算
    if db_task.actual_start_time and db_task.actual_end_time:
        duration = db_task.actual_end_time - db_task.actual_start_time
        db_task.actual_duration_minutes = int(duration.total_seconds() / 60)
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task

def auto_create_cleaning_tasks(db: Session, checkout_date: date) -> List[CleaningTaskModel]:
    """チェックアウト予約から清掃タスクを自動生成"""
    # チェックアウトする予約を取得
    reservations = db.query(Reservation).filter(
        and_(
            Reservation.check_out_date == checkout_date,
            Reservation.reservation_type != "キャンセル"
        )
    ).all()
    
    created_tasks = []
    for reservation in reservations:
        # facility_idがない場合の処理
        if not reservation.facility_id:
            # room_typeから施設を推定
            if reservation.room_type:
                # 施設名で検索
                facility = db.query(Facility).filter(
                    Facility.name == reservation.room_type
                ).first()
                if facility:
                    reservation.facility_id = facility.id
                    db.add(reservation)
                else:
                    # room_typeから施設を作成
                    new_facility = Facility(
                        name=reservation.room_type,
                        is_active=True
                    )
                    db.add(new_facility)
                    db.flush()  # IDを取得するためにflush
                    reservation.facility_id = new_facility.id
                    db.add(reservation)
                    print(f"Created new facility '{reservation.room_type}' for reservation {reservation.id}")
            else:
                # デフォルトの施設IDを設定
                default_facility = db.query(Facility).first()
                if default_facility:
                    reservation.facility_id = default_facility.id
                    db.add(reservation)
                else:
                    # デフォルト施設を作成
                    new_facility = Facility(
                        name="デフォルト施設",
                        is_active=True
                    )
                    db.add(new_facility)
                    db.flush()
                    reservation.facility_id = new_facility.id
                    db.add(reservation)
                    print(f"Created default facility for reservation {reservation.id}")
        
        # 既存タスクがないか確認
        existing = db.query(CleaningTaskModel).filter(
            CleaningTaskModel.reservation_id == reservation.id
        ).first()
        
        if not existing:
            # 施設の清掃設定を取得
            settings = db.query(FacilityCleaningSettingsModel).filter(
                FacilityCleaningSettingsModel.facility_id == reservation.facility_id
            ).first()
            
            # デフォルト値
            duration = 120
            if settings:
                duration = settings.standard_duration_minutes
            
            # タスク作成
            task = CleaningTaskModel(
                reservation_id=reservation.id,
                facility_id=reservation.facility_id,
                checkout_date=checkout_date,
                checkout_time=time(10, 0),  # デフォルト10:00
                scheduled_date=checkout_date,
                scheduled_start_time=time(11, 0),  # デフォルト11:00開始
                scheduled_end_time=time(13, 0),  # デフォルト13:00終了
                estimated_duration_minutes=duration,
                priority=3,
                status=TaskStatus.UNASSIGNED
            )
            
            db.add(task)
            created_tasks.append(task)
    
    db.commit()
    for task in created_tasks:
        db.refresh(task)

    return created_tasks

# ========== シフト関連 ==========

def get_cleaning_shift(db: Session, shift_id: int) -> Optional[CleaningShiftModel]:
    """シフト取得"""
    return db.query(CleaningShiftModel)\
        .options(joinedload(CleaningShiftModel.staff))\
        .options(joinedload(CleaningShiftModel.task))\
        .filter(CleaningShiftModel.id == shift_id).first()

def get_cleaning_shifts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    assigned_date: Optional[date] = None,
    staff_id: Optional[int] = None,
    status: Optional[ShiftStatus] = None
) -> List[CleaningShiftModel]:
    """シフト一覧取得"""
    query = db.query(CleaningShiftModel)\
        .options(joinedload(CleaningShiftModel.staff))\
        .options(joinedload(CleaningShiftModel.task))
    
    if assigned_date:
        query = query.filter(CleaningShiftModel.assigned_date == assigned_date)
    
    if staff_id:
        query = query.filter(CleaningShiftModel.staff_id == staff_id)
    
    if status:
        query = query.filter(CleaningShiftModel.status == status)
    
    return query.order_by(CleaningShiftModel.assigned_date, CleaningShiftModel.scheduled_start_time)\
        .offset(skip).limit(limit).all()

def create_cleaning_shift(db: Session, shift: CleaningShiftCreate) -> CleaningShiftModel:
    """シフト作成（タスクへのスタッフ割当）"""
    # タスクのステータス更新
    task = db.query(CleaningTaskModel).filter(CleaningTaskModel.id == shift.task_id).first()
    if task:
        task.status = TaskStatus.ASSIGNED
        task.updated_at = datetime.utcnow()
    
    # 同じタスクに既に割り当てられているスタッフ数を取得
    existing_shifts = db.query(CleaningShiftModel).filter(
        CleaningShiftModel.task_id == shift.task_id
    ).all()
    num_assigned_staff = len(existing_shifts) + 1
    
    # シフト作成
    db_shift = CleaningShiftModel(**shift.dict())
    db_shift.status = ShiftStatus.SCHEDULED
    db_shift.num_assigned_staff = num_assigned_staff
    
    # スタッフの1棟あたり報酬を取得して賃金計算
    staff = db.query(StaffModel).filter(StaffModel.id == shift.staff_id).first()
    if staff:
        # オプション付きかどうかで報酬を選択
        base_rate = staff.rate_per_property_with_option if shift.is_option_included else staff.rate_per_property
        
        # 人数で等分
        db_shift.calculated_wage = base_rate / num_assigned_staff
        db_shift.transportation_fee = staff.transportation_fee
        db_shift.total_payment = db_shift.calculated_wage + staff.transportation_fee
        
        # 既存のシフトの報酬も更新（人数が増えたため）
        for existing_shift in existing_shifts:
            existing_staff = db.query(StaffModel).filter(StaffModel.id == existing_shift.staff_id).first()
            if existing_staff:
                base_rate = existing_staff.rate_per_property_with_option if existing_shift.is_option_included else existing_staff.rate_per_property
                existing_shift.calculated_wage = base_rate / num_assigned_staff
                existing_shift.num_assigned_staff = num_assigned_staff
                existing_shift.total_payment = existing_shift.calculated_wage + existing_shift.transportation_fee + (existing_shift.bonus or 0)
    
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    return db_shift

def update_cleaning_shift(
    db: Session,
    shift_id: int,
    shift: CleaningShiftUpdate
) -> Optional[CleaningShiftModel]:
    """シフト更新"""
    db_shift = get_cleaning_shift(db, shift_id)
    if not db_shift:
        return None
    
    update_data = shift.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_shift, field, value)
    
    # タスクのステータス連動更新
    if shift.status:
        task = db.query(CleaningTaskModel).filter(CleaningTaskModel.id == db_shift.task_id).first()
        if task:
            if shift.status == ShiftStatus.IN_PROGRESS:
                task.status = TaskStatus.IN_PROGRESS
            elif shift.status == ShiftStatus.COMPLETED:
                task.status = TaskStatus.COMPLETED
            elif shift.status == ShiftStatus.CANCELLED:
                task.status = TaskStatus.UNASSIGNED
            task.updated_at = datetime.utcnow()
    
    # 支払い再計算
    if db_shift.bonus is not None:
        db_shift.total_payment = (db_shift.calculated_wage or 0) + \
                                 (db_shift.transportation_fee or 0) + \
                                 db_shift.bonus
    
    db_shift.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_shift)
    return db_shift

def delete_cleaning_shift(db: Session, shift_id: int) -> bool:
    """シフト削除"""
    db_shift = get_cleaning_shift(db, shift_id)
    if not db_shift:
        return False
    
    task_id = db_shift.task_id
    
    # シフト削除
    db.delete(db_shift)
    
    # 同じタスクの残りのシフトを取得
    remaining_shifts = db.query(CleaningShiftModel).filter(
        CleaningShiftModel.task_id == task_id
    ).all()
    
    if remaining_shifts:
        # 残りのシフトの人数と報酬を再計算
        num_assigned_staff = len(remaining_shifts)
        for shift in remaining_shifts:
            staff = db.query(StaffModel).filter(StaffModel.id == shift.staff_id).first()
            if staff:
                base_rate = staff.rate_per_property_with_option if shift.is_option_included else staff.rate_per_property
                shift.calculated_wage = base_rate / num_assigned_staff
                shift.num_assigned_staff = num_assigned_staff
                shift.total_payment = shift.calculated_wage + shift.transportation_fee + (shift.bonus or 0)
    else:
        # タスクのステータスを未割当に戻す
        task = db.query(CleaningTaskModel).filter(CleaningTaskModel.id == task_id).first()
        if task:
            task.status = TaskStatus.UNASSIGNED
            task.updated_at = datetime.utcnow()
    
    db.commit()
    return True

# ========== 施設清掃設定関連 ==========

def get_facility_cleaning_settings(
    db: Session,
    facility_id: int
) -> Optional[FacilityCleaningSettingsModel]:
    """施設清掃設定取得"""
    return db.query(FacilityCleaningSettingsModel)\
        .filter(FacilityCleaningSettingsModel.facility_id == facility_id).first()

def create_facility_cleaning_settings(
    db: Session,
    settings: FacilityCleaningSettingsCreate
) -> FacilityCleaningSettingsModel:
    """施設清掃設定作成"""
    db_settings = FacilityCleaningSettingsModel(**settings.dict())
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

def update_facility_cleaning_settings(
    db: Session,
    facility_id: int,
    settings: FacilityCleaningSettingsUpdate
) -> Optional[FacilityCleaningSettingsModel]:
    """施設清掃設定更新"""
    db_settings = get_facility_cleaning_settings(db, facility_id)
    if not db_settings:
        return None
    
    update_data = settings.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    
    db_settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_settings)
    return db_settings

# ========== ダッシュボード・統計関連 ==========

def get_cleaning_dashboard_stats(db: Session, target_date: date) -> Dict[str, Any]:
    """清掃ダッシュボード統計取得"""
    # 今日のタスク数
    today_tasks = db.query(func.count(CleaningTaskModel.id))\
        .filter(CleaningTaskModel.scheduled_date == target_date).scalar()
    
    # ステータス別集計
    unassigned = db.query(func.count(CleaningTaskModel.id))\
        .filter(and_(
            CleaningTaskModel.scheduled_date == target_date,
            CleaningTaskModel.status == TaskStatus.UNASSIGNED
        )).scalar()
    
    in_progress = db.query(func.count(CleaningTaskModel.id))\
        .filter(and_(
            CleaningTaskModel.scheduled_date == target_date,
            CleaningTaskModel.status == TaskStatus.IN_PROGRESS
        )).scalar()
    
    completed = db.query(func.count(CleaningTaskModel.id))\
        .filter(and_(
            CleaningTaskModel.scheduled_date == target_date,
            CleaningTaskModel.status == TaskStatus.COMPLETED
        )).scalar()
    
    # アクティブスタッフ数
    active_staff = db.query(func.count(StaffModel.id))\
        .filter(StaffModel.is_active == True).scalar()
    
    # 平均完了時間
    avg_duration = db.query(func.avg(CleaningTaskModel.actual_duration_minutes))\
        .filter(and_(
            CleaningTaskModel.scheduled_date == target_date,
            CleaningTaskModel.status == TaskStatus.COMPLETED
        )).scalar()
    
    return {
        "today_tasks": today_tasks or 0,
        "unassigned_tasks": unassigned or 0,
        "in_progress_tasks": in_progress or 0,
        "completed_tasks": completed or 0,
        "active_staff": active_staff or 0,
        "average_completion_time": avg_duration
    }

def get_staff_performance(
    db: Session,
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """スタッフパフォーマンス取得"""
    results = db.query(
        StaffModel.id,
        StaffModel.name,
        func.count(CleaningShiftModel.id).label("completed_tasks"),
        func.avg(CleaningShiftModel.performance_rating).label("average_rating"),
        func.sum(
            func.julianday(CleaningShiftModel.actual_end_time) -
            func.julianday(CleaningShiftModel.actual_start_time)
        ).label("total_days"),
        func.sum(CleaningShiftModel.total_payment).label("total_earnings")
    ).join(CleaningShiftModel)\
    .filter(and_(
        CleaningShiftModel.assigned_date >= start_date,
        CleaningShiftModel.assigned_date <= end_date,
        CleaningShiftModel.status == ShiftStatus.COMPLETED
    )).group_by(StaffModel.id).all()
    
    performance_list = []
    for result in results:
        performance_list.append({
            "staff_id": result.id,
            "staff_name": result.name,
            "completed_tasks": result.completed_tasks or 0,
            "average_rating": result.average_rating,
            "total_hours": (result.total_days or 0) * 24,  # Convert days to hours
            "total_earnings": result.total_earnings or 0
        })
    
    return performance_list