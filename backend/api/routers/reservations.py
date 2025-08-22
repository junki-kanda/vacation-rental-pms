from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated
from datetime import date

from ..database import get_db
from ..schemas import Reservation, ReservationCreate, ReservationUpdate
from ..crud import (
    get_reservations, get_reservation, create_reservation, 
    update_reservation, get_or_create_facility
)

router = APIRouter(
    prefix="/api/reservations",
    tags=["予約管理"],
    responses={404: {"description": "Not found"}}
)

@router.get(
    "",
    response_model=List[Reservation],
    summary="予約一覧の取得",
    description="指定された条件に基づいて予約の一覧を取得します。複数の条件を組み合わせてフィルタリングが可能です。"
)
def list_reservations(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    ota_name: Annotated[Optional[List[str]], Query(description="OTA名でフィルター（複数指定可）")] = None,
    facility_id: Annotated[Optional[str], Query(description="施設IDでフィルター")] = None,
    room_type: Annotated[Optional[str], Query(description="部屋タイプでフィルター")] = None,
    check_in_date_from: Annotated[Optional[str], Query(description="チェックイン日の開始日（YYYY-MM-DD形式）")] = None,
    check_in_date_to: Annotated[Optional[str], Query(description="チェックイン日の終了日（YYYY-MM-DD形式）")] = None,
    guest_name: Annotated[Optional[str], Query(description="ゲスト名でフィルター（部分一致）")] = None,
    sort_by: Annotated[Optional[str], Query(description="ソートキー（check_in_date, created_at等）")] = None,
    sort_order: Annotated[Optional[str], Query(description="ソート順序（asc: 昇順, desc: 降順）")] = None,
    db: Session = Depends(get_db)
):
    """
    予約一覧を取得
    
    ### フィルター条件:
    - **ota_name**: OTA名でフィルター（複数指定可能）
    - **facility_id**: 特定の施設の予約のみ取得
    - **room_type**: 特定の部屋タイプの予約のみ取得
    - **check_in_date_from/to**: チェックイン日の期間指定
    - **guest_name**: ゲスト名での部分一致検索
    
    ### ソート:
    - **sort_by**: check_in_date, created_at, guest_name等
    - **sort_order**: asc（昇順）またはdesc（降順）
    """
    # 空文字列をNoneに変換
    if ota_name and all(name == "" for name in ota_name):
        ota_name = None
    if guest_name == "":
        guest_name = None
    if room_type == "":
        room_type = None
    
    # facility_idを整数に変換
    facility_id_int = None
    if facility_id and facility_id != "":
        try:
            facility_id_int = int(facility_id)
        except ValueError:
            facility_id_int = None
    
    # 日付文字列をdateオブジェクトに変換
    date_from = None
    date_to = None
    if check_in_date_from and check_in_date_from != "":
        try:
            date_from = date.fromisoformat(check_in_date_from)
        except ValueError:
            date_from = None
    if check_in_date_to and check_in_date_to != "":
        try:
            date_to = date.fromisoformat(check_in_date_to)
        except ValueError:
            date_to = None
        
    reservations = get_reservations(
        db, skip=skip, limit=limit,
        ota_name=ota_name,
        facility_id=facility_id_int,
        room_type=room_type,
        check_in_date_from=date_from,
        check_in_date_to=date_to,
        guest_name=guest_name,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return reservations

@router.get("/{reservation_id}", response_model=Reservation)
def get_reservation_detail(reservation_id: int, db: Session = Depends(get_db)):
    """予約詳細を取得"""
    reservation = get_reservation(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@router.post("", response_model=Reservation)
def create_new_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db)
):
    """予約を作成"""
    # 施設の取得または作成
    facility = get_or_create_facility(
        db,
        name=reservation.room_type.split(" - ")[0] if " - " in reservation.room_type else reservation.room_type,
        room_type_identifier=reservation.room_type
    )
    
    return create_reservation(db, reservation, facility_id=facility.id)

@router.put("/{reservation_id}", response_model=Reservation)
def update_existing_reservation(
    reservation_id: str,
    reservation: ReservationUpdate,
    db: Session = Depends(get_db)
):
    """予約を更新"""
    updated = update_reservation(db, reservation_id, reservation)
    if not updated:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return updated

@router.delete("/{reservation_id}")
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db)
):
    """予約を削除"""
    from ..models import Reservation as ReservationModel
    
    reservation = db.query(ReservationModel).filter(ReservationModel.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    db.delete(reservation)
    db.commit()
    
    return {"message": "Reservation deleted successfully"}