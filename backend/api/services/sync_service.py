"""同期サービス - CSV処理とデータベース同期の統合管理"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
import logging

from .simple_parser import SimpleCSVParser
from .ota_detector import OTADetectorService
from ..schemas import ReservationCreate, SyncLogCreate
from .. import crud

logger = logging.getLogger(__name__)

class SyncService:
    """CSV同期処理を管理するサービス"""
    
    def __init__(self):
        self.parser = None
        self.ota_detector = OTADetectorService()
    
    def process_csv_sync(
        self,
        file_path: str,
        sync_id: int,
        db: Session,
        encoding: str = None
    ) -> Dict[str, any]:
        """
        CSVファイルの同期処理を実行
        
        Args:
            file_path: CSVファイルパス
            sync_id: 同期ログID
            db: データベースセッション
            encoding: ファイルエンコーディング（Noneの場合は自動検出）
        
        Returns:
            処理結果の詳細情報
        """
        result = {
            "success": False,
            "total_rows": 0,
            "processed_rows": 0,
            "new_count": 0,
            "updated_count": 0,
            "error_count": 0,
            "errors": [],
            "detected_encoding": None,
            "encoding_confidence": 0
        }
        
        try:
            # CSVパーサーの初期化と解析（エンコーディング自動検出）
            self.parser = SimpleCSVParser(file_path, encoding=encoding)
            reservations_data, parse_errors = self.parser.parse()
            
            # エンコーディング情報を結果に追加
            if self.parser.detected_encoding:
                result["detected_encoding"] = self.parser.detected_encoding
                result["encoding_confidence"] = self.parser.encoding_confidence
                logger.info(f"Used encoding: {self.parser.detected_encoding} (confidence: {self.parser.encoding_confidence:.2f})")
            
            if parse_errors:
                result["errors"].extend(parse_errors)
                logger.warning(f"CSV parse warnings: {parse_errors}")
            total_rows = len(reservations_data)
            result["total_rows"] = total_rows
            
            # 同期ログの更新
            crud.update_sync_log(
                db,
                sync_id,
                total_rows=total_rows,
                status="processing"
            )
            
            # OTA検出サービスを使用してデータを強化
            enhanced_data = self._enhance_with_ota_detection(reservations_data)
            
            # 各予約データの処理
            for row_data in enhanced_data:
                try:
                    process_result = self._process_reservation_data(
                        row_data, sync_id, db
                    )
                    
                    if process_result["action"] == "created":
                        result["new_count"] += 1
                    elif process_result["action"] == "updated":
                        result["updated_count"] += 1
                    
                    result["processed_rows"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing reservation {row_data.get('reservation_id', 'unknown')}: {str(e)}")
                    result["error_count"] += 1
                    result["errors"].append(f"予約ID {row_data.get('reservation_id', 'unknown')}: {str(e)}")
            
            # コミット
            db.commit()
            
            # 同期ログの完了更新
            crud.update_sync_log(
                db,
                sync_id,
                status="completed",
                processed_rows=result["processed_rows"],
                new_reservations=result["new_count"],
                updated_reservations=result["updated_count"],
                error_rows=result["error_count"]
            )
            
            result["success"] = True
            logger.info(f"Sync completed: {result['new_count']} new, {result['updated_count']} updated, {result['error_count']} errors")
            
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            result["errors"].append(f"同期処理全体エラー: {str(e)}")
            crud.update_sync_log(
                db,
                sync_id,
                status="failed",
                error_message=str(e)
            )
        
        return result
    
    def _enhance_with_ota_detection(self, reservations_data: List[Dict]) -> List[Dict]:
        """OTA検出サービスを使用してデータを強化"""
        enhanced_data = []
        
        for reservation in reservations_data:
            # OTA検出
            ota_result = self.ota_detector.detect_ota(
                reservation.get("ota_name", ""),
                reservation.get("reservation_number", "")
            )
            
            # OTA情報を更新
            reservation["ota_type"] = ota_result["ota_type"]
            reservation["ota_display_name"] = ota_result["display_name"]
            reservation["ota_confidence"] = ota_result["confidence"]
            
            enhanced_data.append(reservation)
        
        return enhanced_data
    
    def _process_reservation_data(
        self, 
        row_data: Dict, 
        sync_id: int, 
        db: Session
    ) -> Dict[str, str]:
        """個別予約データの処理"""
        
        # 施設の取得または作成
        facility_name = row_data.pop("facility_name", None)
        facility_id = None
        
        if facility_name:
            facility = crud.get_or_create_facility(
                db,
                name=facility_name,
                room_type_identifier=row_data.get("room_type", "")
            )
            facility_id = facility.id
        
        # 日付文字列をdateオブジェクトに変換
        if row_data.get("check_in_date") and isinstance(row_data["check_in_date"], str):
            row_data["check_in_date"] = datetime.fromisoformat(row_data["check_in_date"]).date()
        if row_data.get("check_out_date") and isinstance(row_data["check_out_date"], str):
            row_data["check_out_date"] = datetime.fromisoformat(row_data["check_out_date"]).date()
        
        # 既存予約の確認
        existing = crud.get_reservation_by_reservation_id(
            db,
            row_data["reservation_id"]
        )
        
        if existing:
            # 更新処理
            for key, value in row_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.facility_id = facility_id
            existing.sync_id = sync_id
            existing.updated_at = datetime.utcnow()
            return {"action": "updated", "reservation_id": row_data["reservation_id"]}
        else:
            # 新規作成処理
            reservation_create = ReservationCreate(**row_data)
            crud.create_reservation(
                db,
                reservation_create,
                facility_id=facility_id,
                sync_id=sync_id
            )
            return {"action": "created", "reservation_id": row_data["reservation_id"]}
    
    def validate_csv_file(self, file_path: str) -> Dict[str, any]:
        """CSVファイルの検証"""
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "preview_data": []
        }
        
        try:
            path = Path(file_path)
            if not path.exists():
                validation_result["errors"].append("ファイルが存在しません")
                return validation_result
            
            if not path.suffix.lower() == '.csv':
                validation_result["errors"].append("CSVファイルではありません")
                return validation_result
            
            # パーサーで簡易チェック（エンコーディング自動検出）
            parser = SimpleCSVParser(file_path, encoding=None)
            reservations_data, parse_errors = parser.parse()
            
            # エンコーディング情報を検証結果に追加
            if parser.detected_encoding:
                validation_result["detected_encoding"] = parser.detected_encoding
                validation_result["encoding_confidence"] = parser.encoding_confidence
            
            if parse_errors:
                validation_result["warnings"].extend(parse_errors)
            
            if reservations_data:
                # プレビューデータの生成（最初の5行）
                validation_result["preview_data"] = reservations_data[:5]
                validation_result["valid"] = True
            else:
                validation_result["errors"].append("データが読み込めませんでした")
            
        except Exception as e:
            validation_result["errors"].append(f"ファイル検証エラー: {str(e)}")
        
        return validation_result
    
    def get_sync_statistics(self, db: Session, days: int = 30) -> Dict[str, any]:
        """同期統計の取得
        
        Args:
            db: データベースセッション
            days: 統計対象の過去日数（デフォルト30日）
        
        Returns:
            統計情報の辞書
        """
        from datetime import datetime, timedelta
        
        # 日付フィルタリングの実装
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 指定期間内の同期ログを取得
        recent_syncs = db.query(crud.models.SyncLog).filter(
            crud.models.SyncLog.started_at >= start_date,
            crud.models.SyncLog.started_at <= end_date
        ).order_by(
            crud.models.SyncLog.started_at.desc()
        ).all()
        
        # 統計情報の計算
        stats = {
            "period_days": days,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_syncs": len(recent_syncs),
            "successful_syncs": len([s for s in recent_syncs if s.status == "completed"]),
            "failed_syncs": len([s for s in recent_syncs if s.status == "failed"]),
            "processing_syncs": len([s for s in recent_syncs if s.status == "processing"]),
            "total_processed_reservations": sum([s.processed_rows or 0 for s in recent_syncs]),
            "total_new_reservations": sum([s.new_reservations or 0 for s in recent_syncs]),
            "total_updated_reservations": sum([s.updated_reservations or 0 for s in recent_syncs]),
            "total_error_rows": sum([s.error_rows or 0 for s in recent_syncs]),
        }
        
        # 成功率の計算
        stats["success_rate"] = (
            (stats["successful_syncs"] / stats["total_syncs"] * 100) 
            if stats["total_syncs"] > 0 else 0
        )
        
        # 日別統計を追加
        daily_stats = self._calculate_daily_stats(recent_syncs)
        stats["daily_breakdown"] = daily_stats
        
        # 最近の同期情報
        if recent_syncs:
            latest_sync = recent_syncs[0]
            stats["latest_sync"] = {
                "id": latest_sync.id,
                "file_name": latest_sync.file_name,
                "status": latest_sync.status,
                "started_at": latest_sync.started_at.isoformat() if latest_sync.started_at else None,
                "completed_at": latest_sync.completed_at.isoformat() if latest_sync.completed_at else None,
                "processed_rows": latest_sync.processed_rows
            }
        else:
            stats["latest_sync"] = None
        
        return stats
    
    def _calculate_daily_stats(self, syncs: List) -> List[Dict]:
        """日別統計の計算
        
        Args:
            syncs: 同期ログのリスト
        
        Returns:
            日別統計のリスト
        """
        from collections import defaultdict
        from datetime import datetime
        
        daily_data = defaultdict(lambda: {
            "date": None,
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "processed_rows": 0,
            "new_reservations": 0,
            "updated_reservations": 0
        })
        
        for sync in syncs:
            if sync.started_at:
                date_key = sync.started_at.date().isoformat()
                daily_data[date_key]["date"] = date_key
                daily_data[date_key]["total_syncs"] += 1
                
                if sync.status == "completed":
                    daily_data[date_key]["successful_syncs"] += 1
                elif sync.status == "failed":
                    daily_data[date_key]["failed_syncs"] += 1
                
                daily_data[date_key]["processed_rows"] += sync.processed_rows or 0
                daily_data[date_key]["new_reservations"] += sync.new_reservations or 0
                daily_data[date_key]["updated_reservations"] += sync.updated_reservations or 0
        
        # 日付順にソート
        sorted_daily_stats = sorted(daily_data.values(), key=lambda x: x["date"], reverse=True)
        
        return sorted_daily_stats
    
    def get_sync_logs_by_date_range(
        self,
        db: Session,
        start_date: datetime = None,
        end_date: datetime = None,
        status: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """指定日付範囲の同期ログを取得
        
        Args:
            db: データベースセッション
            start_date: 開始日時（Noneの場合は30日前）
            end_date: 終了日時（Noneの場合は現在）
            status: フィルタリングするステータス（"completed", "failed", "processing"）
            limit: 取得する最大件数
        
        Returns:
            同期ログのリスト
        """
        from datetime import datetime, timedelta
        
        # デフォルト値の設定
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        # クエリの構築
        query = db.query(crud.models.SyncLog)
        
        # 日付フィルタ
        query = query.filter(
            crud.models.SyncLog.started_at >= start_date,
            crud.models.SyncLog.started_at <= end_date
        )
        
        # ステータスフィルタ
        if status:
            query = query.filter(crud.models.SyncLog.status == status)
        
        # ソートと件数制限
        syncs = query.order_by(
            crud.models.SyncLog.started_at.desc()
        ).limit(limit).all()
        
        # 結果を辞書形式に変換
        result = []
        for sync in syncs:
            sync_dict = {
                "id": sync.id,
                "sync_type": sync.sync_type,
                "file_name": sync.file_name,
                "status": sync.status,
                "total_rows": sync.total_rows,
                "processed_rows": sync.processed_rows,
                "new_reservations": sync.new_reservations,
                "updated_reservations": sync.updated_reservations,
                "error_rows": sync.error_rows,
                "error_message": sync.error_message,
                "started_at": sync.started_at.isoformat() if sync.started_at else None,
                "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                "duration_seconds": None
            }
            
            # 処理時間の計算
            if sync.started_at and sync.completed_at:
                duration = sync.completed_at - sync.started_at
                sync_dict["duration_seconds"] = duration.total_seconds()
            
            result.append(sync_dict)
        
        return result
    
    def get_sync_summary_by_month(self, db: Session, year: int, month: int) -> Dict:
        """月別同期サマリーの取得
        
        Args:
            db: データベースセッション
            year: 年
            month: 月
        
        Returns:
            月別サマリー情報
        """
        from datetime import datetime
        from calendar import monthrange
        
        # 月の開始日と終了日を計算
        start_date = datetime(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        # 該当月の同期ログを取得
        syncs = db.query(crud.models.SyncLog).filter(
            crud.models.SyncLog.started_at >= start_date,
            crud.models.SyncLog.started_at <= end_date
        ).all()
        
        # サマリー情報の計算
        summary = {
            "year": year,
            "month": month,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_syncs": len(syncs),
            "successful_syncs": len([s for s in syncs if s.status == "completed"]),
            "failed_syncs": len([s for s in syncs if s.status == "failed"]),
            "total_processed_rows": sum([s.processed_rows or 0 for s in syncs]),
            "total_new_reservations": sum([s.new_reservations or 0 for s in syncs]),
            "total_updated_reservations": sum([s.updated_reservations or 0 for s in syncs]),
            "total_error_rows": sum([s.error_rows or 0 for s in syncs]),
            "unique_files": len(set([s.file_name for s in syncs if s.file_name])),
            "average_rows_per_sync": 0,
            "success_rate": 0
        }
        
        # 平均値と成功率の計算
        if summary["total_syncs"] > 0:
            summary["average_rows_per_sync"] = summary["total_processed_rows"] / summary["total_syncs"]
            summary["success_rate"] = (summary["successful_syncs"] / summary["total_syncs"]) * 100
        
        # 週別統計も追加
        weekly_stats = self._calculate_weekly_stats(syncs, year, month)
        summary["weekly_breakdown"] = weekly_stats
        
        return summary
    
    def _calculate_weekly_stats(self, syncs: List, year: int, month: int) -> List[Dict]:
        """週別統計の計算
        
        Args:
            syncs: 同期ログのリスト
            year: 年
            month: 月
        
        Returns:
            週別統計のリスト
        """
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        weekly_data = defaultdict(lambda: {
            "week_number": 0,
            "week_start": None,
            "week_end": None,
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "processed_rows": 0
        })
        
        for sync in syncs:
            if sync.started_at:
                # 週番号を計算（月内での週番号）
                week_number = ((sync.started_at.day - 1) // 7) + 1
                week_key = f"week_{week_number}"
                
                # 週の開始日と終了日を計算
                week_start = datetime(year, month, ((week_number - 1) * 7) + 1)
                week_end = week_start + timedelta(days=6)
                
                weekly_data[week_key]["week_number"] = week_number
                weekly_data[week_key]["week_start"] = week_start.date().isoformat()
                weekly_data[week_key]["week_end"] = week_end.date().isoformat()
                weekly_data[week_key]["total_syncs"] += 1
                
                if sync.status == "completed":
                    weekly_data[week_key]["successful_syncs"] += 1
                elif sync.status == "failed":
                    weekly_data[week_key]["failed_syncs"] += 1
                
                weekly_data[week_key]["processed_rows"] += sync.processed_rows or 0
        
        # 週番号順にソート
        sorted_weekly_stats = sorted(weekly_data.values(), key=lambda x: x["week_number"])
        
        return sorted_weekly_stats