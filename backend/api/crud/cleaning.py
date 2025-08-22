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
    task_data = task.dict()
    
    # デフォルト時間の設定
    if not task_data.get('scheduled_start_time'):
        task_data['scheduled_start_time'] = time(11, 0)  # デフォルト11:00
    if not task_data.get('scheduled_end_time'):
        task_data['scheduled_end_time'] = time(16, 0)  # デフォルト16:00
    if not task_data.get('estimated_duration_minutes'):
        task_data['estimated_duration_minutes'] = 300  # デフォルト5時間
    
    db_task = CleaningTaskModel(**task_data)
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

import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class TaskCreationError(Exception):
    """清掃タスク作成時のエラー"""
    def __init__(self, message: str, reservation_id: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.reservation_id = reservation_id
        self.details = details or {}

class TaskCreationResult:
    """タスク作成結果"""
    def __init__(self):
        self.created_tasks: List[CleaningTaskModel] = []
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.stats = {
            'total_reservations': 0,
            'created_tasks': 0,
            'skipped_existing': 0,
            'created_facilities': 0,
            'errors': 0
        }

def auto_create_cleaning_tasks(db: Session, checkout_date: date) -> TaskCreationResult:
    """チェックアウト予約から清掃タスクを自動生成
    
    Args:
        db: データベースセッション
        checkout_date: チェックアウト日
        
    Returns:
        TaskCreationResult: 作成結果の詳細情報
    """
    result = TaskCreationResult()
    
    try:
        # バリデーション
        if not checkout_date:
            raise ValueError("checkout_date is required")
        
        # チェックアウトする予約を取得
        reservations = db.query(Reservation).filter(
            and_(
                Reservation.check_out_date == checkout_date,
                Reservation.reservation_type != "キャンセル"
            )
        ).all()
        
        result.stats['total_reservations'] = len(reservations)
        logger.info(f"Found {len(reservations)} reservations for checkout on {checkout_date}")
        
        if not reservations:
            logger.info(f"No reservations found for checkout date {checkout_date}")
            return result
        
        # 各予約に対してタスクを作成
        for reservation in reservations:
            try:
                # 予約データの基本バリデーション
                if not reservation.id:
                    logger.warning(f"Reservation without ID found, skipping")
                    continue
                
                # 施設IDの処理（既存タスクがあってもfacility_idは必要）
                facility_id = _ensure_facility_exists(db, reservation, result)
                if not facility_id:
                    error = {
                        'reservation_id': reservation.id,
                        'error': 'Failed to resolve facility',
                        'details': {
                            'reservation_number': reservation.reservation_number,
                            'room_type': reservation.room_type
                        }
                    }
                    result.errors.append(error)
                    result.stats['errors'] += 1
                    continue
                
                # 既存タスクがないか確認
                existing = db.query(CleaningTaskModel).filter(
                    CleaningTaskModel.reservation_id == reservation.id
                ).first()
                
                if existing:
                    logger.debug(f"Task already exists for reservation {reservation.id}, skipping task creation")
                    result.stats['skipped_existing'] += 1
                    continue
                
                # タスク作成
                task = _create_task_from_reservation(db, reservation, facility_id, checkout_date)
                result.created_tasks.append(task)
                result.stats['created_tasks'] += 1
                
                logger.info(f"Created cleaning task {task.id} for reservation {reservation.id}")
                
            except TaskCreationError as e:
                error = {
                    'reservation_id': e.reservation_id or reservation.id,
                    'error': str(e),
                    'details': e.details
                }
                result.errors.append(error)
                result.stats['errors'] += 1
                logger.error(f"Task creation error for reservation {reservation.id}: {e}")
                
            except Exception as e:
                error = {
                    'reservation_id': reservation.id,
                    'error': f"Unexpected error: {str(e)}",
                    'details': {
                        'reservation_number': getattr(reservation, 'reservation_number', None),
                        'room_type': getattr(reservation, 'room_type', None)
                    }
                }
                result.errors.append(error)
                result.stats['errors'] += 1
                logger.error(f"Unexpected error for reservation {reservation.id}: {e}", exc_info=True)
        
        # 変更をコミット（タスク作成、施設作成、予約更新など）
        db.commit()
        
        # 作成されたタスクをリフレッシュ
        for task in result.created_tasks:
            db.refresh(task)
            
        if result.created_tasks:
            logger.info(f"Successfully created {len(result.created_tasks)} cleaning tasks")
        else:
            logger.info("No new tasks were created")
            
        if result.stats['created_facilities'] > 0:
            logger.info(f"Created {result.stats['created_facilities']} new facilities")
            
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during task creation: {e}", exc_info=True)
        result.errors.append({
            'error': 'Database error',
            'details': {'message': str(e)}
        })
        result.stats['errors'] += 1
        
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in auto_create_cleaning_tasks: {e}", exc_info=True)
        result.errors.append({
            'error': 'System error',
            'details': {'message': str(e)}
        })
        result.stats['errors'] += 1
    
    return result


def _ensure_facility_exists(db: Session, reservation: Reservation, result: TaskCreationResult) -> Optional[int]:
    """施設の存在を確認し、必要に応じて作成"""
    try:
        # 既に facility_id がある場合
        if reservation.facility_id:
            facility = db.query(Facility).filter(Facility.id == reservation.facility_id).first()
            if facility:
                return reservation.facility_id
            else:
                logger.warning(f"Invalid facility_id {reservation.facility_id} for reservation {reservation.id}")
                reservation.facility_id = None
        
        # room_type から施設を検索/作成
        if reservation.room_type is not None:
            # 施設名のバリデーション（空文字や空白のみをチェック）
            if len(reservation.room_type.strip()) == 0:
                raise TaskCreationError(
                    "Room type is empty",
                    reservation.id,
                    {'room_type': reservation.room_type}
                )
            
            facility = db.query(Facility).filter(
                Facility.name == reservation.room_type
            ).first()
            
            if facility:
                reservation.facility_id = facility.id
                db.add(reservation)
                return facility.id
            else:
                
                # 新しい施設を作成
                new_facility = Facility(
                    name=reservation.room_type.strip(),
                    is_active=True
                )
                db.add(new_facility)
                db.flush()  # IDを取得
                
                reservation.facility_id = new_facility.id
                db.add(reservation)
                result.stats['created_facilities'] += 1
                
                logger.info(f"Created new facility '{reservation.room_type}' (ID: {new_facility.id}) for reservation {reservation.id}")
                return new_facility.id
        
        # デフォルト施設の処理
        default_facility = db.query(Facility).filter(Facility.is_active == True).first()
        if default_facility:
            reservation.facility_id = default_facility.id
            db.add(reservation)
            result.warnings.append({
                'reservation_id': reservation.id,
                'warning': 'Used default facility due to missing room_type',
                'details': {'facility_name': default_facility.name}
            })
            return default_facility.id
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
            result.stats['created_facilities'] += 1
            
            result.warnings.append({
                'reservation_id': reservation.id,
                'warning': 'Created default facility',
                'details': {'facility_name': new_facility.name}
            })
            
            logger.info(f"Created default facility (ID: {new_facility.id}) for reservation {reservation.id}")
            return new_facility.id
            
    except TaskCreationError:
        # Re-raise TaskCreationError to be handled by the main function
        raise
    except Exception as e:
        logger.error(f"Unexpected error ensuring facility for reservation {reservation.id}: {e}")
        return None


def _create_task_from_reservation(
    db: Session, 
    reservation: Reservation, 
    facility_id: int, 
    checkout_date: date
) -> CleaningTaskModel:
    """予約情報からタスクを作成"""
    try:
        # 施設の清掃設定を取得
        settings = db.query(FacilityCleaningSettingsModel).filter(
            FacilityCleaningSettingsModel.facility_id == facility_id
        ).first()
        
        # デフォルト値
        duration = 300  # デフォルト5時間
        start_time = time(11, 0)  # デフォルト11:00開始
        end_time = time(16, 0)  # デフォルト16:00終了
        
        if settings:
            duration = settings.standard_duration_minutes or duration
            if settings.preferred_start_time:
                start_time = settings.preferred_start_time
            if settings.preferred_end_time:
                end_time = settings.preferred_end_time
        
        # 優先度の決定
        priority = 3  # デフォルト
        if hasattr(reservation, 'num_adults') and reservation.num_adults:
            # ゲスト数に基づく優先度調整
            if reservation.num_adults + (reservation.num_children or 0) > 6:
                priority = 2  # 大人数の場合は高優先度
        
        # タスク作成
        task = CleaningTaskModel(
            reservation_id=reservation.id,
            facility_id=facility_id,
            checkout_date=checkout_date,
            checkout_time=time(10, 0),  # デフォルト10:00チェックアウト
            scheduled_date=checkout_date,
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
            estimated_duration_minutes=duration,
            priority=priority,
            status=TaskStatus.UNASSIGNED
        )
        
        # タスクのバリデーション
        if task.scheduled_start_time >= task.scheduled_end_time:
            raise TaskCreationError(
                "Invalid schedule times",
                reservation.id,
                {
                    'start_time': str(task.scheduled_start_time),
                    'end_time': str(task.scheduled_end_time)
                }
            )
        
        db.add(task)
        db.flush()  # IDを取得
        
        return task
        
    except Exception as e:
        raise TaskCreationError(
            f"Failed to create task: {str(e)}",
            reservation.id,
            {'facility_id': facility_id}
        )

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

def unassign_task_from_staff(db: Session, task_id: int) -> bool:
    """タスクからスタッフ/グループの割り当てを解除"""
    # タスクに関連するすべてのシフトを取得
    shifts = db.query(CleaningShiftModel).filter(
        CleaningShiftModel.task_id == task_id
    ).all()
    
    if not shifts:
        return False
    
    # すべてのシフトを削除
    for shift in shifts:
        db.delete(shift)
    
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