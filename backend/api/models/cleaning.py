from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Date, Boolean, ForeignKey, Time, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base

class TaskStatus(enum.Enum):
    """清掃タスクのステータス"""
    UNASSIGNED = "unassigned"  # 未割当
    ASSIGNED = "assigned"      # 割当済
    IN_PROGRESS = "in_progress"  # 作業中
    COMPLETED = "completed"    # 完了
    VERIFIED = "verified"      # 検証済
    CANCELLED = "cancelled"    # キャンセル

class ShiftStatus(enum.Enum):
    """シフトのステータス"""
    SCHEDULED = "scheduled"    # 予定
    CONFIRMED = "confirmed"    # 確定
    IN_PROGRESS = "in_progress"  # 作業中
    COMPLETED = "completed"    # 完了
    CANCELLED = "cancelled"    # キャンセル

class Staff(Base):
    """清掃スタッフマスタテーブル"""
    __tablename__ = "cleaning_staff"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    name_kana = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100), unique=True, nullable=True)
    
    # スキル・能力
    skill_level = Column(Integer, default=1)  # 1-5のスキルレベル
    can_drive = Column(Boolean, default=False)  # 運転可能か
    has_car = Column(Boolean, default=False)  # 車保有か
    
    # 対応可能施設（JSON配列でfacility_idのリストを保存）
    available_facilities = Column(JSON, default=list)
    
    # 稼働可能情報（JSON形式で曜日・時間帯を保存）
    # 例: {"monday": {"start": "09:00", "end": "18:00"}, ...}
    available_schedule = Column(JSON, default=dict)
    
    # 報酬設定（1棟あたり）
    rate_per_property = Column(Float, default=3000)  # 1棟あたりの基本報酬
    rate_per_property_with_option = Column(Float, default=4000)  # オプション付き1棟あたりの報酬
    transportation_fee = Column(Float, default=0)  # 交通費
    
    # ステータス
    is_active = Column(Boolean, default=True)
    
    # メタデータ
    notes = Column(Text)  # 備考
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    shifts = relationship("CleaningShift", back_populates="staff", overlaps="tasks,assigned_staff")
    tasks = relationship("CleaningTask", secondary="cleaning_shifts", back_populates="assigned_staff", overlaps="shifts")

class CleaningTask(Base):
    """清掃タスクテーブル"""
    __tablename__ = "cleaning_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    
    # タスク情報
    checkout_date = Column(Date, nullable=False, index=True)
    checkout_time = Column(Time)
    scheduled_date = Column(Date, nullable=False, index=True)  # 清掃予定日
    scheduled_start_time = Column(Time)  # 清掃開始予定時刻
    scheduled_end_time = Column(Time)  # 清掃終了予定時刻
    
    # 必要時間と優先度
    estimated_duration_minutes = Column(Integer, default=120)  # 推定所要時間（分）
    priority = Column(Integer, default=3)  # 1-5の優先度（1が最高）
    
    # ステータス
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.UNASSIGNED, nullable=False)
    
    # 実績
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    actual_duration_minutes = Column(Integer)
    
    # 検証
    verified_by = Column(Integer, ForeignKey("cleaning_staff.id"))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # 追加情報
    special_instructions = Column(Text)  # 特別指示
    supplies_needed = Column(JSON)  # 必要な備品リスト
    photos_before = Column(JSON)  # 清掃前写真URLリスト
    photos_after = Column(JSON)  # 清掃後写真URLリスト
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    reservation = relationship("Reservation", backref="cleaning_tasks")
    facility = relationship("Facility", backref="cleaning_tasks")
    shifts = relationship("CleaningShift", back_populates="task")
    assigned_staff = relationship("Staff", secondary="cleaning_shifts", back_populates="tasks", overlaps="shifts")
    verifier = relationship("Staff", foreign_keys=[verified_by])

class CleaningShift(Base):
    """シフト（スタッフとタスクの割当）テーブル"""
    __tablename__ = "cleaning_shifts"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("cleaning_staff.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("cleaning_tasks.id"), nullable=False)
    
    # 割当情報
    assigned_date = Column(Date, nullable=False, index=True)
    scheduled_start_time = Column(Time, nullable=False)
    scheduled_end_time = Column(Time, nullable=False)
    
    # ステータス
    status = Column(SQLEnum(ShiftStatus), default=ShiftStatus.SCHEDULED, nullable=False)
    
    # 実績
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    check_in_location = Column(JSON)  # {"lat": 35.123, "lng": 139.456}
    check_out_location = Column(JSON)
    
    # 報酬
    calculated_wage = Column(Float)  # 計算済み賃金（1棟あたり報酬÷担当人数）
    is_option_included = Column(Boolean, default=False)  # オプション料金適用か
    num_assigned_staff = Column(Integer, default=1)  # 同じタスクに割り当てられたスタッフ数
    transportation_fee = Column(Float)  # 交通費
    bonus = Column(Float, default=0)  # ボーナス
    total_payment = Column(Float)  # 合計支払額
    
    # 評価
    performance_rating = Column(Integer)  # 1-5の評価
    performance_notes = Column(Text)
    
    # その他
    notes = Column(Text)
    cancellation_reason = Column(Text)
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))  # 作成者（管理者名など）
    
    # リレーション
    staff = relationship("Staff", back_populates="shifts", overlaps="assigned_staff,tasks")
    task = relationship("CleaningTask", back_populates="shifts", overlaps="assigned_staff,tasks")

class FacilityCleaningSettings(Base):
    """施設別清掃設定テーブル"""
    __tablename__ = "facility_cleaning_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), unique=True, nullable=False)
    
    # 清掃時間設定
    standard_duration_minutes = Column(Integer, default=120)  # 標準清掃時間（分）
    deep_cleaning_duration_minutes = Column(Integer, default=180)  # 念入り清掃時間（分）
    minimum_interval_hours = Column(Integer, default=2)  # 最小間隔（チェックアウトから清掃開始まで）
    
    # チェックリスト（JSON配列）
    cleaning_checklist = Column(JSON, default=list)
    # 例: [
    #   {"area": "リビング", "tasks": ["掃除機", "拭き掃除", "ゴミ回収"]},
    #   {"area": "浴室", "tasks": ["浴槽清掃", "排水口清掃", "鏡磨き"]}
    # ]
    
    # 必要備品（JSON配列）
    required_supplies = Column(JSON, default=list)
    # 例: ["掃除機", "モップ", "洗剤", "タオル"]
    
    # 特記事項
    special_instructions = Column(Text)
    access_instructions = Column(Text)  # アクセス方法（鍵の場所など）
    parking_info = Column(Text)  # 駐車場情報
    
    # 優先スタッフ（JSON配列でstaff_idのリストを保存）
    preferred_staff_ids = Column(JSON, default=list)
    
    # 料金設定
    cleaning_fee = Column(Float)  # 清掃料金（ゲストに請求する場合）
    staff_payment = Column(Float)  # スタッフへの支払額
    
    # フラグ
    requires_inspection = Column(Boolean, default=False)  # 検査必須か
    auto_assign = Column(Boolean, default=True)  # 自動割当対象か
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    facility = relationship("Facility", backref="cleaning_settings", uselist=False)