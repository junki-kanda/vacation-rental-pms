from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .property import Facility

# Reservation Schemas
class ReservationBase(BaseModel):
    reservation_id: str
    reservation_type: str
    reservation_number: Optional[str] = None
    ota_name: str
    ota_type: Optional[str] = None
    room_type: str
    check_in_date: date
    check_out_date: date
    reservation_date: Optional[datetime] = None
    guest_name: str
    guest_name_kana: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
    num_adults: int = 1
    num_children: int = 0
    num_infants: int = 0  # 幼児人数
    total_amount: Optional[float] = None
    commission: Optional[float] = None
    net_amount: Optional[float] = None
    adult_rate: Optional[float] = None
    child_rate: Optional[float] = None
    infant_rate: Optional[float] = None
    adult_amount: Optional[float] = None
    child_amount: Optional[float] = None
    infant_amount: Optional[float] = None
    # 追加フィールド（ねっぱんCSV対応）
    nights: Optional[int] = 1
    rooms: Optional[int] = 1
    meal_plan: Optional[str] = None
    payment_method: Optional[str] = None
    booker_name: Optional[str] = None
    booker_name_kana: Optional[str] = None
    plan_name: Optional[str] = None
    plan_code: Optional[str] = None
    checkin_time: Optional[str] = None
    cancel_date: Optional[date] = None
    # オプション・その他
    option_items: Optional[str] = None
    option_amount: Optional[float] = None
    point_amount: Optional[float] = None
    point_discount: Optional[float] = None
    # 追加情報
    postal_code: Optional[str] = None
    address: Optional[str] = None
    member_number: Optional[str] = None
    company_info: Optional[str] = None
    reservation_route: Optional[str] = None
    # 備考
    notes: Optional[str] = None
    questions_answers: Optional[str] = None
    change_history: Optional[str] = None
    memo: Optional[str] = None

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(ReservationBase):
    pass

class Reservation(ReservationBase):
    id: int
    facility_id: Optional[int] = None
    facility: Optional[Facility] = None
    created_at: datetime
    updated_at: datetime
    sync_id: Optional[int] = None
    
    class Config:
        from_attributes = True

# Filter Schemas
class ReservationFilter(BaseModel):
    ota_name: Optional[str] = None
    facility_id: Optional[int] = None
    check_in_date_from: Optional[date] = None
    check_in_date_to: Optional[date] = None
    guest_name: Optional[str] = None