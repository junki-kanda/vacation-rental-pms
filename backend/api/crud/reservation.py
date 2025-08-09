from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from datetime import date, datetime
from typing import List, Optional
from ..models import Reservation
from ..schemas import ReservationCreate, ReservationUpdate

def get_reservation(db: Session, reservation_id: int):
    return db.query(Reservation).options(joinedload(Reservation.facility)).filter(Reservation.id == reservation_id).first()

def get_reservation_by_reservation_id(db: Session, reservation_id: str):
    return db.query(Reservation).options(joinedload(Reservation.facility)).filter(Reservation.reservation_id == reservation_id).first()

def get_reservations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    ota_name: Optional[List[str]] = None,
    facility_id: Optional[int] = None,
    room_type: Optional[str] = None,
    check_in_date_from: Optional[date] = None,
    check_in_date_to: Optional[date] = None,
    guest_name: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
):
    query = db.query(Reservation).options(joinedload(Reservation.facility))
    
    if ota_name and len(ota_name) > 0:
        query = query.filter(Reservation.ota_name.in_(ota_name))
    if facility_id:
        query = query.filter(Reservation.facility_id == facility_id)
    if room_type:
        query = query.filter(Reservation.room_type.contains(room_type))
    if check_in_date_from:
        query = query.filter(Reservation.check_in_date >= check_in_date_from)
    if check_in_date_to:
        query = query.filter(Reservation.check_in_date <= check_in_date_to)
    if guest_name:
        query = query.filter(Reservation.guest_name.contains(guest_name))
    
    # ソート処理
    if sort_by and hasattr(Reservation, sort_by):
        sort_column = getattr(Reservation, sort_by)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        # デフォルトはチェックイン日の降順
        query = query.order_by(Reservation.check_in_date.desc())
    
    return query.offset(skip).limit(limit).all()

def create_reservation(db: Session, reservation: ReservationCreate, facility_id: Optional[int] = None, sync_id: Optional[int] = None):
    db_reservation = Reservation(
        **reservation.dict(),
        facility_id=facility_id,
        sync_id=sync_id
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def update_reservation(db: Session, reservation_id: str, reservation: ReservationUpdate):
    # IDが数値の場合は主キーで検索、文字列の場合はreservation_idで検索
    try:
        id_int = int(reservation_id)
        db_reservation = db.query(Reservation).filter(Reservation.id == id_int).first()
    except ValueError:
        db_reservation = get_reservation_by_reservation_id(db, reservation_id)
    
    if db_reservation:
        for key, value in reservation.dict(exclude_unset=True).items():
            setattr(db_reservation, key, value)
        db_reservation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_reservation)
    return db_reservation