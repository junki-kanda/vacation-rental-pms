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
        """同期統計の取得"""
        # 過去指定日数の同期ログを取得
        # TODO: 日付フィルタリングの実装
        recent_syncs = db.query(crud.models.SyncLog).order_by(
            crud.models.SyncLog.started_at.desc()
        ).limit(100).all()
        
        stats = {
            "total_syncs": len(recent_syncs),
            "successful_syncs": len([s for s in recent_syncs if s.status == "completed"]),
            "failed_syncs": len([s for s in recent_syncs if s.status == "failed"]),
            "total_processed_reservations": sum([s.processed_rows or 0 for s in recent_syncs]),
            "total_new_reservations": sum([s.new_reservations or 0 for s in recent_syncs]),
            "total_updated_reservations": sum([s.updated_reservations or 0 for s in recent_syncs]),
        }
        
        stats["success_rate"] = (
            (stats["successful_syncs"] / stats["total_syncs"] * 100) 
            if stats["total_syncs"] > 0 else 0
        )
        
        return stats