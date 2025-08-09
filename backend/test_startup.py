"""スタートアップテスト - インポートエラーの確認"""

import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

print("1. Checking database module...")
try:
    from api.database import Base, engine, get_db
    print("   [OK] Database module loaded successfully")
except ImportError as e:
    print(f"   [ERROR] Database module error: {e}")
    sys.exit(1)

print("\n2. Checking models...")
try:
    from api.models import Base, Reservation, Facility, SyncLog
    print("   [OK] Models loaded successfully")
except ImportError as e:
    print(f"   [ERROR] Models error: {e}")
    sys.exit(1)

print("\n3. Checking schemas...")
try:
    from api.schemas import ReservationCreate, SyncLogCreate
    print("   [OK] Schemas loaded successfully")
except ImportError as e:
    print(f"   [ERROR] Schemas error: {e}")
    sys.exit(1)

print("\n4. Checking services...")
try:
    from api.services import SyncService
    print("   [OK] Services loaded successfully")
except ImportError as e:
    print(f"   [ERROR] Services error: {e}")
    sys.exit(1)

print("\n5. Checking routers...")
try:
    from api.routers import sync_router, dashboard_router
    print("   [OK] Routers loaded successfully")
except ImportError as e:
    print(f"   [ERROR] Routers error: {e}")
    sys.exit(1)

print("\n6. Checking main app...")
try:
    from api.main import app
    print("   [OK] Main app loaded successfully")
except ImportError as e:
    print(f"   [ERROR] Main app error: {e}")
    sys.exit(1)

print("\n[SUCCESS] All modules loaded successfully!")
print("\nYou can now start the server with:")
print("python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")