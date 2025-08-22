from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import date, datetime

from ..database import get_db
from ..schemas import DashboardStats
from ..crud import (
    get_dashboard_stats, 
    get_monthly_stats,
    get_monthly_comparison,
    get_daily_stats,
    get_ota_breakdown
)
from ..models import Reservation

router = APIRouter(
    prefix="/api/dashboard",
    tags=["ダッシュボード"],
    responses={404: {"description": "Not found"}}
)

@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="ダッシュボード統計情報の取得",
    description="本日のチェックイン/アウト、宿泊者数、稼働率などのリアルタイム統計を取得します"
)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    ダッシュボードの統計情報を取得
    
    ### 取得できる情報:
    - **today_checkins**: 本日のチェックイン棟数
    - **today_checkouts**: 本日のチェックアウト棟数
    - **total_guests_today**: 本日の宿泊者数合計
    - **occupancy_rate**: 現在の稼働率（%）
    - **recent_reservations**: 最近の予約（10件）
    - **sync_status**: 最新の同期状態
    """
    return get_dashboard_stats(db)

@router.get("/calendar/reservations")
def get_calendar_reservations(
    start_date: date,
    end_date: date,
    room_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """カレンダー表示用の予約データを取得"""
    query = db.query(Reservation).filter(
        and_(
            Reservation.check_in_date <= end_date,
            Reservation.check_out_date >= start_date
        )
    )
    
    if room_type:
        query = query.filter(Reservation.room_type == room_type)
    
    reservations = query.all()
    
    # カレンダー表示用にフォーマット
    calendar_data = []
    for res in reservations:
        calendar_data.append({
            "id": res.id,
            "title": f"{res.guest_name} ({res.ota_name})",
            "start": res.check_in_date.isoformat(),
            "end": res.check_out_date.isoformat(),
            "room_type": res.room_type,
            "reservation_type": res.reservation_type,
            "ota_name": res.ota_name,
            "ota_type": res.ota_type,
            "guest_count": res.num_adults + res.num_children + res.num_infants,
            "num_adults": res.num_adults,
            "num_children": res.num_children,
            "num_infants": res.num_infants
        })
    
    return calendar_data

@router.get("/room-types")
def get_room_types(db: Session = Depends(get_db)):
    """部屋タイプ一覧を取得"""
    room_types = db.query(Reservation.room_type).distinct().order_by(Reservation.room_type).all()
    return [rt[0] for rt in room_types if rt[0]]

@router.get("/ota-names")
def get_ota_names(db: Session = Depends(get_db)):
    """OTA名一覧を取得"""
    ota_names = db.query(Reservation.ota_name).distinct().filter(
        Reservation.ota_name.isnot(None),
        Reservation.ota_name != ""
    ).order_by(Reservation.ota_name).all()
    return [ota[0] for ota in ota_names if ota[0]]

@router.get("/monthly-stats")
def get_monthly_statistics(
    year: int = Query(default=None, description="Year for statistics"),
    month: int = Query(default=None, description="Month for statistics (1-12)"),
    db: Session = Depends(get_db)
):
    """月間統計情報を取得"""
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    return get_monthly_stats(db, year, month)

@router.get("/monthly-comparison")
def get_monthly_comparison_data(
    year: int = Query(default=None, description="Year for comparison"),
    month: int = Query(default=None, description="Month for comparison (1-12)"),
    db: Session = Depends(get_db)
):
    """月間実績・予算・前年比較データを取得"""
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    return get_monthly_comparison(db, year, month)

@router.get("/daily-stats")
def get_daily_statistics(
    year: int = Query(default=None, description="Year for statistics"),
    month: int = Query(default=None, description="Month for statistics (1-12)"),
    db: Session = Depends(get_db)
):
    """月間の日別統計を取得"""
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    return get_daily_stats(db, year, month)

@router.get("/ota-breakdown")
def get_ota_breakdown_data(
    year: int = Query(default=None, description="Year for breakdown"),
    month: int = Query(default=None, description="Month for breakdown (1-12)"),
    db: Session = Depends(get_db)
):
    """OTA別の月間統計を取得"""
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    return get_ota_breakdown(db, year, month)