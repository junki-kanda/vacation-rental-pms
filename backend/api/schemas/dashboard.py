from pydantic import BaseModel
from typing import List, Optional
from .reservation import Reservation
from .sync_log import SyncLog

# Dashboard Schemas
class DashboardStats(BaseModel):
    today_checkins: int
    today_checkouts: int
    total_guests_today: int
    occupancy_rate: float
    recent_reservations: List[Reservation]
    sync_status: Optional[SyncLog] = None