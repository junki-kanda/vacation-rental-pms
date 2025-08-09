from sqlalchemy.orm import Session
from datetime import datetime
from ..models import SyncLog
from ..schemas import SyncLogCreate

def create_sync_log(db: Session, sync_log: SyncLogCreate):
    db_sync = SyncLog(**sync_log.dict())
    db.add(db_sync)
    db.commit()
    db.refresh(db_sync)
    return db_sync

def update_sync_log(db: Session, sync_id: int, **kwargs):
    db_sync = db.query(SyncLog).filter(SyncLog.id == sync_id).first()
    if db_sync:
        for key, value in kwargs.items():
            setattr(db_sync, key, value)
        if "status" in kwargs and kwargs["status"] in ["completed", "failed"]:
            db_sync.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_sync)
    return db_sync

def get_latest_sync_log(db: Session):
    return db.query(SyncLog).order_by(SyncLog.started_at.desc()).first()