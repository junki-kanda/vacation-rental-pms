from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(String(50), unique=True, index=True)
    reservation_type = Column(String(20))  # 予約/変更/キャンセル
    reservation_number = Column(String(50))
    
    # OTA情報
    ota_name = Column(String(100), index=True)  # 予約サイト名称
    ota_type = Column(String(50))  # Booking.com, Expedia等
    
    # 施設情報
    facility_id = Column(Integer, ForeignKey("facilities.id"))
    room_type = Column(String(100))  # 部屋タイプ名称
    
    # 日付情報
    check_in_date = Column(Date, index=True)
    check_out_date = Column(Date, index=True)
    reservation_date = Column(DateTime)
    
    # 宿泊者情報
    guest_name = Column(String(100))
    guest_name_kana = Column(String(100))
    guest_phone = Column(String(20))
    guest_email = Column(String(100))
    num_adults = Column(Integer, default=1)
    num_children = Column(Integer, default=0)
    num_infants = Column(Integer, default=0)  # 幼児人数
    
    # 料金情報
    total_amount = Column(Float)
    commission = Column(Float)
    net_amount = Column(Float)
    adult_rate = Column(Float)  # 大人単価
    child_rate = Column(Float)  # 子供単価
    infant_rate = Column(Float)  # 幼児単価
    adult_amount = Column(Float)  # 大人合計額
    child_amount = Column(Float)  # 子供合計額
    infant_amount = Column(Float)  # 幼児合計額
    
    # 追加フィールド（ねっぱんCSV対応）
    nights = Column(Integer, default=1)  # 泊数
    rooms = Column(Integer, default=1)  # 室数
    meal_plan = Column(String(100))  # 食事
    payment_method = Column(String(100))  # 決済方法
    booker_name = Column(String(100))  # 予約者氏名
    booker_name_kana = Column(String(100))  # 予約者氏名カタカナ
    plan_name = Column(String(200))  # 商品プラン名称
    plan_code = Column(String(50))  # 商品プランコード
    checkin_time = Column(String(10))  # チェックイン時刻
    cancel_date = Column(Date)  # 予約キャンセル日
    
    # オプション・その他料金
    option_items = Column(Text)  # その他明細（オプション項目）
    option_amount = Column(Float)  # その他合計額
    point_amount = Column(Float)  # ポイント額
    point_discount = Column(Float)  # ポイント割引額
    
    # 追加情報
    postal_code = Column(String(10))  # 郵便番号
    address = Column(String(200))  # 住所1
    member_number = Column(String(50))  # 会員番号
    company_info = Column(String(200))  # 法人情報
    reservation_route = Column(String(100))  # 予約経路
    
    # その他
    notes = Column(Text)  # 備考
    questions_answers = Column(Text)  # 質問回答
    change_history = Column(Text)  # 変更履歴
    memo = Column(Text)  # メモ
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_id = Column(Integer, ForeignKey("sync_logs.id"))
    
    # リレーション
    facility = relationship("Facility", back_populates="reservations")
    sync_log = relationship("SyncLog", back_populates="reservations")