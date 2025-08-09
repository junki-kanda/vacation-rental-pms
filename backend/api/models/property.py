from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Facility(Base):
    __tablename__ = "facilities"
    
    id = Column(Integer, primary_key=True, index=True)
    # 施設名（予約データの部屋タイプ名と一致）
    name = Column(String(100), unique=True, index=True)
    
    # 施設グループ（シリーズ・ブランド名）
    facility_group = Column(String(100))  # 例: 「Villa」「別荘」など
    
    # 施設詳細情報
    address = Column(String(200))
    phone = Column(String(20))
    
    # 清掃・料金設定
    cleaning_fee = Column(Float)  # 清掃料金
    base_rate = Column(Float)  # 基本料金
    
    # 施設設備情報
    max_guests = Column(Integer, default=4)  # 最大宿泊人数
    bedrooms = Column(Integer, default=1)  # 寝室数
    bathrooms = Column(Integer, default=1)  # バスルーム数
    
    # ステータス
    is_active = Column(Boolean, default=True)  # 稼働中かどうか
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    reservations = relationship("Reservation", back_populates="facility")
    
    @property
    def display_name(self):
        """表示用の名前（グループ名付き）"""
        if self.facility_group:
            return f"[{self.facility_group}] {self.name}"
        return self.name