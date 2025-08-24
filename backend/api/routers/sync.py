from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import shutil
import os

from ..database import get_db
from ..schemas import SyncLog, SyncLogCreate
from ..crud import create_sync_log, update_sync_log
from ..services import SyncService

# リクエストボディ用のスキーマ
class ProcessLocalRequest(BaseModel):
    filename: str

router = APIRouter(prefix="/api/sync", tags=["sync"])

# 設定
CSV_DIR = os.getenv("CSV_DIR", "./data/csv")
Path(CSV_DIR).mkdir(parents=True, exist_ok=True)

sync_service = SyncService()

def process_csv_background(file_path: str, sync_id: int):
    """バックグラウンドでCSV処理を実行"""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        sync_service.process_csv_sync(file_path, sync_id, db)
    finally:
        db.close()

@router.post("/upload")
async def upload_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """CSVファイルをアップロードして同期処理を開始"""
    # ファイル検証
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # ファイル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = Path(CSV_DIR) / f"{timestamp}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 同期ログの作成
    sync_log = create_sync_log(
        db,
        SyncLogCreate(
            sync_type="manual",
            file_name=file.filename,
            status="processing"
        )
    )
    
    # バックグラウンドで同期処理
    background_tasks.add_task(
        process_csv_background,
        str(file_path),
        sync_log.id
    )
    
    return {
        "message": "CSV upload started",
        "sync_id": sync_log.id,
        "file_name": file.filename
    }

@router.post("/trigger")
async def trigger_sync(
    file_path: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """指定されたCSVファイルで同期処理を実行"""
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # 同期ログの作成
    sync_log = create_sync_log(
        db,
        SyncLogCreate(
            sync_type="manual",
            file_name=path.name,
            status="processing"
        )
    )
    
    # バックグラウンドで同期処理
    background_tasks.add_task(
        process_csv_background,
        str(path),
        sync_log.id
    )
    
    return {
        "message": "Sync started",
        "sync_id": sync_log.id
    }

@router.get("/status/{sync_id}", response_model=SyncLog)
def get_sync_status(sync_id: int, db: Session = Depends(get_db)):
    """同期処理のステータスを取得"""
    from ..models import SyncLog as SyncLogModel
    sync_log = db.query(SyncLogModel).filter(SyncLogModel.id == sync_id).first()
    if not sync_log:
        raise HTTPException(status_code=404, detail="Sync log not found")
    return sync_log

@router.get("/validate")
def validate_csv_file(file_path: str):
    """CSVファイルの検証"""
    result = sync_service.validate_csv_file(file_path)
    return result

@router.get("/list-csv")
def list_csv_files():
    """利用可能なCSVファイルをリスト"""
    csv_files = []
    csv_path = Path(CSV_DIR)
    if csv_path.exists():
        for file in csv_path.glob("*.csv"):
            csv_files.append({
                "filename": file.name,
                "path": str(file),
                "size": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
    return {"files": csv_files}

@router.post("/process-local")
async def process_local_csv(
    request: ProcessLocalRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """ローカルのCSVファイルを処理"""
    filename = request.filename
    file_path = Path(CSV_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    
    # 同期ログの作成
    sync_log = create_sync_log(
        db,
        SyncLogCreate(
            sync_type="manual",
            file_name=filename,
            status="processing"
        )
    )
    
    # バックグラウンドで同期処理
    background_tasks.add_task(
        process_csv_background,
        str(file_path),
        sync_log.id
    )
    
    return {
        "message": "Processing started",
        "sync_id": sync_log.id,
        "filename": filename
    }

@router.get("/statistics")
def get_sync_statistics(db: Session = Depends(get_db)):
    """同期統計を取得"""
    stats = sync_service.get_sync_statistics(db)
    return stats

@router.post("/preview")
async def preview_csv(
    file: UploadFile = File(...),
    rows: int = 10
):
    """CSVファイルの内容をプレビュー（エンコーディング自動検出付き）"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # 一時ファイルに保存
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name
    
    try:
        # 検証とプレビューデータ取得
        validation_result = sync_service.validate_csv_file(tmp_path)
        
        # プレビュー用に指定行数まで取得
        from ..services.simple_parser import SimpleCSVParser
        parser = SimpleCSVParser(tmp_path, encoding=None)
        preview_data, errors = parser.parse()
        
        result = {
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "detected_encoding": parser.detected_encoding,
            "encoding_confidence": parser.encoding_confidence,
            "total_rows": len(preview_data),
            "preview_rows": preview_data[:rows] if preview_data else [],
            "headers": parser.headers
        }
        
        return result
        
    finally:
        # 一時ファイルを削除
        os.unlink(tmp_path)