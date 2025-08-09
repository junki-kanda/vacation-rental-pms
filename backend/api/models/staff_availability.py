"""スタッフ出勤可能日管理モデル"""

from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class StaffAvailability(Base):
    """スタッフ月別出勤可能日テーブル"""
    __tablename__ = "staff_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("cleaning_staff.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # 各日の出勤可否（1-31日）
    day_1 = Column(Boolean, default=True)
    day_2 = Column(Boolean, default=True)
    day_3 = Column(Boolean, default=True)
    day_4 = Column(Boolean, default=True)
    day_5 = Column(Boolean, default=True)
    day_6 = Column(Boolean, default=True)
    day_7 = Column(Boolean, default=True)
    day_8 = Column(Boolean, default=True)
    day_9 = Column(Boolean, default=True)
    day_10 = Column(Boolean, default=True)
    day_11 = Column(Boolean, default=True)
    day_12 = Column(Boolean, default=True)
    day_13 = Column(Boolean, default=True)
    day_14 = Column(Boolean, default=True)
    day_15 = Column(Boolean, default=True)
    day_16 = Column(Boolean, default=True)
    day_17 = Column(Boolean, default=True)
    day_18 = Column(Boolean, default=True)
    day_19 = Column(Boolean, default=True)
    day_20 = Column(Boolean, default=True)
    day_21 = Column(Boolean, default=True)
    day_22 = Column(Boolean, default=True)
    day_23 = Column(Boolean, default=True)
    day_24 = Column(Boolean, default=True)
    day_25 = Column(Boolean, default=True)
    day_26 = Column(Boolean, default=True)
    day_27 = Column(Boolean, default=True)
    day_28 = Column(Boolean, default=True)
    day_29 = Column(Boolean, default=True)
    day_30 = Column(Boolean, default=True)
    day_31 = Column(Boolean, default=True)
    
    # メタデータ
    created_at = Column(Date, default=datetime.utcnow)
    updated_at = Column(Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    staff = relationship("Staff", backref="availability_records")
    
    # 複合ユニーク制約（同じスタッフの同じ年月は1レコードのみ）
    __table_args__ = (
        UniqueConstraint('staff_id', 'year', 'month', name='_staff_year_month_uc'),
    )