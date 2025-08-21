"""清掃タスク同期サービス

予約データと清掃タスクを同期し、変更を検知してアラートを生成する
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Dict, Any, Tuple
from datetime import datetime, date, time, timedelta
from enum import Enum

from ..models.cleaning import (
    CleaningTask as CleaningTaskModel,
    CleaningShift as CleaningShiftModel,
    TaskStatus,
    ShiftStatus
)
from ..models.reservation import Reservation
from ..models.property import Facility


class AlertType(Enum):
    """アラートタイプ"""
    TASK_CREATED = "task_created"          # 新規タスク作成
    TASK_CANCELLED = "task_cancelled"      # タスクキャンセル（予約キャンセル）
    TASK_MODIFIED = "task_modified"        # タスク変更（日時変更）
    CONFLICT_DETECTED = "conflict_detected"  # 割当済みタスクへの影響
    STAFF_REASSIGN_NEEDED = "staff_reassign_needed"  # スタッフ再割当必要


class CleaningSyncService:
    """清掃タスク同期サービス"""
    
    def __init__(self, db: Session):
        self.db = db
        self.alerts: List[Dict[str, Any]] = []
        
    def sync_all_tasks(self) -> Dict[str, Any]:
        """全清掃タスクを最新の予約データと同期
        
        Returns:
            同期結果とアラートのサマリー
        """
        # 統計情報の初期化
        stats = {
            "tasks_created": 0,
            "tasks_cancelled": 0,
            "tasks_modified": 0,
            "conflicts_detected": 0,
            "total_alerts": 0
        }
        
        # 1. アクティブな予約を全て取得（今日以降のチェックアウト）
        today = date.today()
        active_reservations = self.db.query(Reservation).filter(
            and_(
                Reservation.check_out_date >= today,
                Reservation.reservation_type != "キャンセル"
            )
        ).all()
        
        # 2. 既存の清掃タスクを全て取得（完了済み以外）
        existing_tasks = self.db.query(CleaningTaskModel).filter(
            and_(
                CleaningTaskModel.scheduled_date >= today,
                CleaningTaskModel.status != TaskStatus.COMPLETED,
                CleaningTaskModel.status != TaskStatus.VERIFIED
            )
        ).all()
        
        # 予約IDをキーとしたマップを作成
        reservation_map = {r.id: r for r in active_reservations}
        task_map = {t.reservation_id: t for t in existing_tasks}
        
        # 3. 新規タスクの作成（予約があるがタスクがない）
        for reservation in active_reservations:
            if reservation.id not in task_map:
                task = self._create_task_from_reservation(reservation)
                if task:
                    stats["tasks_created"] += 1
                    self._add_alert(
                        AlertType.TASK_CREATED,
                        f"新規清掃タスクを作成: {reservation.room_type or '施設'} - {reservation.check_out_date}",
                        {
                            "reservation_id": reservation.id,
                            "facility_name": reservation.room_type,
                            "checkout_date": str(reservation.check_out_date),
                            "guest_name": reservation.guest_name
                        }
                    )
        
        # 4. キャンセル検知とタスクの処理
        for task in existing_tasks:
            reservation = reservation_map.get(task.reservation_id)
            
            if not reservation or reservation.reservation_type == "キャンセル":
                # 予約がキャンセルされた
                if task.status == TaskStatus.ASSIGNED:
                    # 既に割当済みの場合は警告
                    stats["conflicts_detected"] += 1
                    self._add_alert(
                        AlertType.CONFLICT_DETECTED,
                        f"割当済みタスクの予約がキャンセルされました",
                        {
                            "task_id": task.id,
                            "facility_id": task.facility_id,
                            "scheduled_date": str(task.scheduled_date),
                            "assigned_staff": self._get_assigned_staff_names(task.id)
                        }
                    )
                
                # タスクをキャンセル状態に
                task.status = TaskStatus.CANCELLED
                stats["tasks_cancelled"] += 1
                self._add_alert(
                    AlertType.TASK_CANCELLED,
                    f"予約キャンセルによりタスクをキャンセル",
                    {"task_id": task.id, "scheduled_date": str(task.scheduled_date)}
                )
            
            # 5. 日時変更の検知
            elif reservation:
                modified = False
                changes = []
                
                # チェックアウト日の変更
                if task.checkout_date != reservation.check_out_date:
                    changes.append(f"チェックアウト日: {task.checkout_date} → {reservation.check_out_date}")
                    task.checkout_date = reservation.check_out_date
                    task.scheduled_date = reservation.check_out_date
                    modified = True
                
                # 施設の変更（room_type変更）
                if reservation.room_type and task.facility_id:
                    facility = self.db.query(Facility).filter(Facility.id == task.facility_id).first()
                    if facility and facility.name != reservation.room_type:
                        changes.append(f"施設: {facility.name} → {reservation.room_type}")
                        # 新しい施設を検索または作成
                        new_facility = self._get_or_create_facility(reservation.room_type)
                        task.facility_id = new_facility.id
                        modified = True
                
                if modified:
                    stats["tasks_modified"] += 1
                    
                    # 割当済みの場合は特別な警告
                    if task.status == TaskStatus.ASSIGNED:
                        stats["conflicts_detected"] += 1
                        self._add_alert(
                            AlertType.STAFF_REASSIGN_NEEDED,
                            f"割当済みタスクの内容が変更されました。再確認が必要です。",
                            {
                                "task_id": task.id,
                                "changes": changes,
                                "assigned_staff": self._get_assigned_staff_names(task.id)
                            }
                        )
                    else:
                        self._add_alert(
                            AlertType.TASK_MODIFIED,
                            f"タスク内容を更新: {', '.join(changes)}",
                            {"task_id": task.id, "changes": changes}
                        )
        
        # 6. 変更をコミット
        self.db.commit()
        
        # 結果のサマリー作成
        stats["total_alerts"] = len(self.alerts)
        
        return {
            "success": True,
            "stats": stats,
            "alerts": self.alerts,
            "sync_time": datetime.now().isoformat()
        }
    
    def _create_task_from_reservation(self, reservation: Reservation) -> CleaningTaskModel:
        """予約から清掃タスクを作成"""
        # facility_idの解決
        facility_id = reservation.facility_id
        if not facility_id:
            if reservation.room_type:
                facility = self._get_or_create_facility(reservation.room_type)
                facility_id = facility.id
                reservation.facility_id = facility_id
            else:
                # デフォルト施設を使用
                facility = self._get_or_create_facility("デフォルト施設")
                facility_id = facility.id
                reservation.facility_id = facility_id
        
        # タスク作成
        task = CleaningTaskModel(
            reservation_id=reservation.id,
            facility_id=facility_id,
            checkout_date=reservation.check_out_date,
            checkout_time=time(10, 0),  # デフォルト10:00
            scheduled_date=reservation.check_out_date,
            scheduled_start_time=time(11, 0),  # デフォルト11:00開始
            scheduled_end_time=time(16, 0),  # デフォルト16:00終了
            estimated_duration_minutes=300,  # デフォルト5時間
            priority=3,
            status=TaskStatus.UNASSIGNED
        )
        
        self.db.add(task)
        self.db.flush()  # IDを取得
        return task
    
    def _get_or_create_facility(self, name: str) -> Facility:
        """施設を取得または作成"""
        facility = self.db.query(Facility).filter(Facility.name == name).first()
        if not facility:
            facility = Facility(name=name, is_active=True)
            self.db.add(facility)
            self.db.flush()
        return facility
    
    def _get_assigned_staff_names(self, task_id: int) -> List[str]:
        """タスクに割り当てられたスタッフ名のリストを取得"""
        shifts = self.db.query(CleaningShiftModel).filter(
            CleaningShiftModel.task_id == task_id
        ).all()
        
        staff_names = []
        for shift in shifts:
            if shift.staff and shift.staff.name:
                staff_names.append(shift.staff.name)
        
        return staff_names
    
    def _add_alert(self, alert_type: AlertType, message: str, details: Dict[str, Any] = None):
        """アラートを追加"""
        alert = {
            "type": alert_type.value,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.alerts.append(alert)
    
    def get_sync_preview(self) -> Dict[str, Any]:
        """同期のプレビュー（実際には変更を行わない）
        
        Returns:
            同期した場合の変更内容のプレビュー
        """
        # トランザクションを開始するが、最後にロールバック
        savepoint = self.db.begin_nested()
        
        try:
            result = self.sync_all_tasks()
            savepoint.rollback()  # 変更を破棄
            return result
        except Exception as e:
            savepoint.rollback()
            raise e