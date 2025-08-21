from .reservations import router as reservations_router
from .properties import router as properties_router
from .sync import router as sync_router
from .dashboard import router as dashboard_router
from .cleaning import router as cleaning_router
from .staff_groups import router as staff_groups_router

__all__ = ["reservations_router", "properties_router", "sync_router", "dashboard_router", "cleaning_router", "staff_groups_router"]