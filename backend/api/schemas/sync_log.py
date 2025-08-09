from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Sync Log Schemas
class SyncLogBase(BaseModel):
    sync_type: str
    file_name: str
    status: str = "processing"

class SyncLogCreate(SyncLogBase):
    pass

class SyncLog(SyncLogBase):
    id: int
    file_path: Optional[str] = None
    total_rows: int = 0
    processed_rows: int = 0
    new_reservations: int = 0
    updated_reservations: int = 0
    error_rows: int = 0
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True