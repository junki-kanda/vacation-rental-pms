from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from ..models import Reservation, Facility
from .sync_log import get_latest_sync_log

def get_dashboard_stats(db: Session):
    today = date.today()
    
    # 本日のチェックイン（棟数でカウント）
    today_checkins = db.query(func.count(func.distinct(Reservation.facility_id))).filter(
        Reservation.check_in_date == today
    ).scalar()
    
    # 本日のチェックアウト（棟数でカウント）
    today_checkouts = db.query(func.count(func.distinct(Reservation.facility_id))).filter(
        Reservation.check_out_date == today
    ).scalar()
    
    # 本日の宿泊者数
    total_guests_today = db.query(
        func.sum(Reservation.num_adults + Reservation.num_children + Reservation.num_infants)
    ).filter(
        and_(
            Reservation.check_in_date <= today,
            Reservation.check_out_date > today
        )
    ).scalar() or 0
    
    # 稼働率計算（全施設数に対する予約施設数）
    total_facilities = db.query(func.count(Facility.id)).filter(
        Facility.is_active == True
    ).scalar() or 1
    occupied_facilities = db.query(func.count(func.distinct(Reservation.facility_id))).filter(
        and_(
            Reservation.check_in_date <= today,
            Reservation.check_out_date > today,
            Reservation.reservation_type != "キャンセル"
        )
    ).scalar() or 0
    occupancy_rate = (occupied_facilities / total_facilities) * 100 if total_facilities > 0 else 0
    
    # 最近の予約（直近10件）
    recent_reservations = db.query(Reservation).order_by(
        Reservation.created_at.desc()
    ).limit(10).all()
    
    # 最新の同期状態
    sync_status = get_latest_sync_log(db)
    
    return {
        "today_checkins": today_checkins or 0,
        "today_checkouts": today_checkouts or 0,
        "total_guests_today": int(total_guests_today),
        "occupancy_rate": round(occupancy_rate, 1),
        "recent_reservations": recent_reservations,
        "sync_status": sync_status
    }

def get_monthly_stats(db: Session, year: int, month: int) -> Dict[str, Any]:
    """月間統計情報を取得"""
    
    # 月の開始日と終了日を計算
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # 月間の予約データを取得
    monthly_reservations = db.query(Reservation).filter(
        and_(
            Reservation.check_in_date <= end_date,
            Reservation.check_out_date >= start_date,
            Reservation.reservation_type != 'キャンセル'
        )
    ).all()
    
    # 月間売上高
    total_revenue = sum([r.total_amount or 0 for r in monthly_reservations])
    
    # 月間の延べ宿泊数（泊数×室数）
    total_room_nights = sum([
        (min(r.check_out_date, end_date) - max(r.check_in_date, start_date)).days
        for r in monthly_reservations
    ])
    
    # 平均宿泊単価（ADR: Average Daily Rate）
    adr = total_revenue / total_room_nights if total_room_nights > 0 else 0
    
    # 稼働率（月間の延べ室数に対する販売室数の割合）
    total_rooms = db.query(func.sum(Facility.total_rooms)).scalar() or 1
    days_in_month = (end_date - start_date).days + 1
    available_room_nights = total_rooms * days_in_month
    occupancy_rate = (total_room_nights / available_room_nights * 100) if available_room_nights > 0 else 0
    
    # RevPAR (Revenue Per Available Room)
    revpar = adr * (occupancy_rate / 100)
    
    return {
        "year": year,
        "month": month,
        "total_revenue": total_revenue,
        "total_reservations": len(monthly_reservations),
        "total_room_nights": total_room_nights,
        "adr": round(adr, 0),
        "occupancy_rate": round(occupancy_rate, 1),
        "revpar": round(revpar, 0)
    }

def get_monthly_comparison(db: Session, year: int, month: int) -> Dict[str, Any]:
    """月間実績・予算・前年比較データを取得"""
    
    # 今月の実績
    current_stats = get_monthly_stats(db, year, month)
    
    # 前年同月の実績
    last_year_stats = get_monthly_stats(db, year - 1, month)
    
    # 予算データ（ダミー）
    budget_data = {
        "year": year,
        "month": month,
        "total_revenue": 8000000,  # 800万円
        "adr": 25000,  # 2.5万円
        "occupancy_rate": 75.0,  # 75%
        "revpar": 18750
    }
    
    return {
        "current": current_stats,
        "budget": budget_data,
        "last_year": last_year_stats,
        "variance": {
            "revenue_vs_budget": ((current_stats["total_revenue"] - budget_data["total_revenue"]) / budget_data["total_revenue"] * 100) if budget_data["total_revenue"] > 0 else 0,
            "revenue_vs_last_year": ((current_stats["total_revenue"] - last_year_stats["total_revenue"]) / last_year_stats["total_revenue"] * 100) if last_year_stats["total_revenue"] > 0 else 0,
            "occupancy_vs_budget": current_stats["occupancy_rate"] - budget_data["occupancy_rate"],
            "occupancy_vs_last_year": current_stats["occupancy_rate"] - last_year_stats["occupancy_rate"],
            "adr_vs_budget": ((current_stats["adr"] - budget_data["adr"]) / budget_data["adr"] * 100) if budget_data["adr"] > 0 else 0,
            "adr_vs_last_year": ((current_stats["adr"] - last_year_stats["adr"]) / last_year_stats["adr"] * 100) if last_year_stats["adr"] > 0 else 0,
        }
    }

def get_daily_stats(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """月間の日別統計を取得"""
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        # その日の予約数（チェックイン）
        checkins = db.query(func.count(Reservation.id)).filter(
            and_(
                Reservation.check_in_date == current_date,
                Reservation.reservation_type != 'キャンセル'
            )
        ).scalar() or 0
        
        # その日の稼働室数
        occupied = db.query(func.count(func.distinct(Reservation.facility_id))).filter(
            and_(
                Reservation.check_in_date <= current_date,
                Reservation.check_out_date > current_date,
                Reservation.reservation_type != 'キャンセル'
            )
        ).scalar() or 0
        
        # その日の売上
        revenue = db.query(func.sum(Reservation.total_amount)).filter(
            and_(
                Reservation.check_in_date == current_date,
                Reservation.reservation_type != 'キャンセル'
            )
        ).scalar() or 0
        
        daily_stats.append({
            "date": current_date.isoformat(),
            "checkins": checkins,
            "occupied_rooms": occupied,
            "revenue": revenue
        })
        
        current_date += timedelta(days=1)
    
    return daily_stats

def get_ota_breakdown(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """OTA別の月間統計を取得"""
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # OTA別の集計
    ota_stats = db.query(
        Reservation.ota_name,
        func.count(Reservation.id).label('reservation_count'),
        func.sum(Reservation.total_amount).label('total_revenue'),
        func.sum(Reservation.num_adults + Reservation.num_children + Reservation.num_infants).label('total_guests')
    ).filter(
        and_(
            Reservation.check_in_date <= end_date,
            Reservation.check_out_date >= start_date,
            Reservation.reservation_type != 'キャンセル'
        )
    ).group_by(Reservation.ota_name).all()
    
    breakdown = []
    for stat in ota_stats:
        breakdown.append({
            "ota_name": stat.ota_name or "直接予約",
            "reservation_count": stat.reservation_count or 0,
            "total_revenue": stat.total_revenue or 0,
            "total_guests": stat.total_guests or 0,
            "average_revenue": (stat.total_revenue / stat.reservation_count) if stat.reservation_count > 0 else 0
        })
    
    # 売上高で降順ソート
    breakdown.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    return breakdown