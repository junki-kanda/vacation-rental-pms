"""
needs_revision ステータスの処理フローテスト
"""
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from api.database import Base, get_db
from api.main import app
from api.models.cleaning import CleaningTask, TaskStatus, CleaningShift
from api.models.property import Facility
from api.models.reservation import Reservation

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_needs_revision.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def setup_database():
    """テストデータベースセットアップ"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(setup_database):
    """データベースセッション"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(setup_database):
    """FastAPIテストクライアント"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_task_revision_request(client: TestClient, db_session: Session):
    """タスクの修正要求テスト"""
    # テストデータの準備
    facility = Facility(
        name="テスト施設",
        address="テスト住所",
        max_guests=4
    )
    db_session.add(facility)
    db_session.flush()
    
    # 予約データも作成（CleaningTaskに必要）
    reservation = Reservation(
        reservation_id="TEST001",
        facility_id=facility.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        guest_name="テストゲスト"
    )
    db_session.add(reservation)
    db_session.flush()
    
    task = CleaningTask(
        reservation_id=reservation.id,
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.ASSIGNED,
        special_instructions="初期備考"
    )
    db_session.add(task)
    db_session.commit()
    
    # 修正要求API呼び出し
    revision_reason = "清掃範囲が不明確です"
    response = client.post(
        f"/api/cleaning/tasks/{task.id}/revision",
        params={"revision_reason": revision_reason}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task.id
    assert data["revision_reason"] == revision_reason
    
    # データベースの確認
    db_session.refresh(task)
    assert task.status == TaskStatus.NEEDS_REVISION
    assert "【修正要求】清掃範囲が不明確です" in (task.special_instructions or "")


def test_task_revision_request_with_existing_notes(client: TestClient, db_session: Session):
    """既存の備考があるタスクの修正要求テスト"""
    facility = Facility(
        name="テスト施設",
        address="テスト住所",
        max_guests=4
    )
    db_session.add(facility)
    db_session.flush()
    
    task = CleaningTask(
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.ASSIGNED,
        notes="既存の備考"
    )
    db_session.add(task)
    db_session.commit()
    
    revision_reason = "時間が不適切です"
    response = client.post(
        f"/api/cleaning/tasks/{task.id}/revision",
        params={"revision_reason": revision_reason}
    )
    
    assert response.status_code == 200
    
    db_session.refresh(task)
    assert task.status == TaskStatus.NEEDS_REVISION
    assert "既存の備考" in task.notes
    assert "【修正要求】時間が不適切です" in task.notes


def test_get_tasks_needing_revision(client: TestClient, db_session: Session):
    """要修正タスク一覧取得テスト"""
    # テストデータの準備
    facility = Facility(
        name="テスト施設",
        address="テスト住所",
        max_guests=4
    )
    db_session.add(facility)
    db_session.flush()
    
    # 要修正タスク
    task1 = CleaningTask(
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.NEEDS_REVISION,
        notes="【修正要求】確認が必要"
    )
    
    # 通常タスク
    task2 = CleaningTask(
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=2),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.ASSIGNED
    )
    
    db_session.add_all([task1, task2])
    db_session.commit()
    
    # API呼び出し
    response = client.get("/api/cleaning/tasks/needs-revision")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == task1.id
    assert data[0]["status"] == TaskStatus.NEEDS_REVISION.value


def test_get_tasks_needing_revision_by_facility(client: TestClient, db_session: Session):
    """施設別要修正タスク一覧取得テスト"""
    # テストデータの準備
    facility1 = Facility(
        name="テスト施設1",
        address="テスト住所1",
        max_guests=4
    )
    facility2 = Facility(
        name="テスト施設2",
        address="テスト住所2",
        max_guests=6
    )
    db_session.add_all([facility1, facility2])
    db_session.flush()
    
    # 要修正タスク（施設1）
    task1 = CleaningTask(
        facility_id=facility1.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.NEEDS_REVISION
    )
    
    # 要修正タスク（施設2）
    task2 = CleaningTask(
        facility_id=facility2.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.NEEDS_REVISION
    )
    
    db_session.add_all([task1, task2])
    db_session.commit()
    
    # 施設1のみ取得
    response = client.get(
        "/api/cleaning/tasks/needs-revision",
        params={"facility_id": facility1.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == task1.id


def test_resolve_task_revision(client: TestClient, db_session: Session):
    """タスクの修正対応完了テスト"""
    # テストデータの準備
    facility = Facility(
        name="テスト施設",
        address="テスト住所",
        max_guests=4
    )
    db_session.add(facility)
    db_session.flush()
    
    task = CleaningTask(
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.NEEDS_REVISION,
        notes="【修正要求】時間調整が必要"
    )
    db_session.add(task)
    db_session.commit()
    
    # 修正対応完了API呼び出し
    resolution_notes = "清掃時間を11:00-15:00に変更しました"
    response = client.post(
        f"/api/cleaning/tasks/{task.id}/resolve-revision",
        params={"resolution_notes": resolution_notes}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task.id
    assert data["resolution_notes"] == resolution_notes
    
    # データベースの確認
    db_session.refresh(task)
    assert task.status == TaskStatus.UNASSIGNED
    assert "【修正対応完了】清掃時間を11:00-15:00に変更しました" in task.notes


def test_resolve_task_revision_invalid_status(client: TestClient, db_session: Session):
    """要修正状態でないタスクの修正対応完了エラーテスト"""
    facility = Facility(
        name="テスト施設",
        address="テスト住所",
        max_guests=4
    )
    db_session.add(facility)
    db_session.flush()
    
    task = CleaningTask(
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.ASSIGNED  # 要修正ではない
    )
    db_session.add(task)
    db_session.commit()
    
    response = client.post(
        f"/api/cleaning/tasks/{task.id}/resolve-revision",
        params={"resolution_notes": "修正完了"}
    )
    
    assert response.status_code == 400
    assert "not in needs_revision status" in response.json()["detail"]


def test_task_status_update_with_unassignment(client: TestClient, db_session: Session):
    """needs_revisionステータス更新時の割り当て解除テスト"""
    from api.models.cleaning import CleaningShift, ShiftStatus
    
    # テストデータの準備
    facility = Facility(
        name="テスト施設",
        address="テスト住所",
        max_guests=4
    )
    db_session.add(facility)
    db_session.flush()
    
    task = CleaningTask(
        facility_id=facility.id,
        checkout_date=date.today(),
        scheduled_date=date.today() + timedelta(days=1),
        estimated_duration_minutes=180,
        priority=3,
        status=TaskStatus.ASSIGNED
    )
    db_session.add(task)
    db_session.flush()
    
    # シフトを作成（タスクが割り当て済み状態を作る）
    shift = CleaningShift(
        staff_id=None,
        group_id=1,
        task_id=task.id,
        assigned_date=date.today() + timedelta(days=1),
        status=ShiftStatus.SCHEDULED
    )
    db_session.add(shift)
    db_session.commit()
    
    # needs_revisionに変更
    response = client.patch(
        f"/api/cleaning/tasks/{task.id}/status",
        params={"status": "needs_revision"}
    )
    
    assert response.status_code == 200
    
    # シフトが削除されていることを確認
    remaining_shifts = db_session.query(CleaningShift).filter(
        CleaningShift.task_id == task.id
    ).all()
    assert len(remaining_shifts) == 0
    
    # タスクのステータスが変更されていることを確認
    db_session.refresh(task)
    assert task.status == TaskStatus.NEEDS_REVISION


def test_revision_request_not_found_task(client: TestClient, db_session: Session):
    """存在しないタスクの修正要求エラーテスト"""
    response = client.post(
        "/api/cleaning/tasks/99999/revision",
        params={"revision_reason": "テスト"}
    )
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_resolve_revision_not_found_task(client: TestClient, db_session: Session):
    """存在しないタスクの修正対応完了エラーテスト"""
    response = client.post(
        "/api/cleaning/tasks/99999/resolve-revision",
        params={"resolution_notes": "テスト"}
    )
    
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]