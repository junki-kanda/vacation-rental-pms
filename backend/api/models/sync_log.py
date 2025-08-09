from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(20))  # manual/auto
    file_name = Column(String(200))
    file_path = Column(String(500))
    
    status = Column(String(20))  # processing/completed/failed
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    new_reservations = Column(Integer, default=0)
    updated_reservations = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # リレーション
    reservations = relationship("Reservation", back_populates="sync_log")