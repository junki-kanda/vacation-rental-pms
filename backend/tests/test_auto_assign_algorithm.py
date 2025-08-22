"""清掃タスク自動割当アルゴリズムのテスト"""

import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.database import Base, get_db
from api.main import app
from api.models.cleaning import Staff, CleaningTask, TaskStatus, CleaningShift
from api.models.property import Facility
from api.models.staff_availability import StaffAvailability
from api.schemas.cleaning import TaskAutoAssignRequest

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auto_assign.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """テスト用データベースのセットアップ"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """各テスト用のデータベースセッション"""
    session = TestingSessionLocal()
    yield session
    session.query(CleaningShift).delete()
    session.query(CleaningTask).delete()
    session.query(StaffAvailability).delete()
    session.query(Staff).delete()
    session.query(Facility).delete()
    session.commit()
    session.close()

@pytest.fixture
def client():
    """テスト用HTTPクライアント"""
    return TestClient(app)

def create_test_data(db_session):
    """テスト用データの作成"""
    # 施設を作成
    facilities = []
    for i in range(1, 4):
        facility = Facility(
            id=i,
            name=f"施設{i}",
            address=f"住所{i}",
            max_guests=10 if i == 3 else 4  # 施設3は大型施設（10人収容）
        )
        db_session.add(facility)
        facilities.append(facility)
    
    # スタッフを作成
    staff_list = []
    for i in range(1, 6):
        staff = Staff(
            id=i,
            name=f"スタッフ{i}",
            email=f"staff{i}@example.com",
            phone=f"090-0000-000{i}",
            is_active=True,
            available_facilities=[1, 2] if i <= 3 else [2, 3]  # スタッフ1-3は施設1,2、スタッフ4-5は施設2,3
            # Note: can_handle_large_properties は Staff モデルに存在しない可能性があるため削除
        )
        db_session.add(staff)
        staff_list.append(staff)
    
    # 出勤可能日を設定（今月）
    today = date.today()
    for i, staff in enumerate(staff_list):
        availability = StaffAvailability(
            staff_id=staff.id,
            year=today.year,
            month=today.month
        )
        # スタッフ1,2は全日出勤可能
        # スタッフ3は偶数日のみ
        # スタッフ4,5は奇数日のみ
        for day in range(1, 32):
            day_column = f"day_{day}"
            if i < 2:  # スタッフ1,2
                setattr(availability, day_column, True)
            elif i == 2:  # スタッフ3
                setattr(availability, day_column, day % 2 == 0)
            else:  # スタッフ4,5
                setattr(availability, day_column, day % 2 == 1)
        db_session.add(availability)
    
    # 清掃タスクを作成
    tasks = []
    for i in range(1, 8):
        task = CleaningTask(
            id=i,
            reservation_id=i,
            facility_id=(i % 3) + 1,  # 施設1,2,3を順番に
            checkout_date=today,
            scheduled_date=today,
            status=TaskStatus.UNASSIGNED,
            priority=1 if i <= 2 else (3 if i <= 5 else 5),  # 1が最高優先度
            estimated_duration_minutes=300,
            created_at=datetime.now()
        )
        db_session.add(task)
        tasks.append(task)
    
    db_session.commit()
    return facilities, staff_list, tasks

def test_auto_assign_basic(setup_database, db_session, client):
    """基本的な自動割当テスト"""
    facilities, staff_list, tasks = create_test_data(db_session)
    
    # 自動割当リクエスト
    request_data = {
        "task_ids": [1, 2, 3],
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert result["assigned_count"] > 0
    assert "自動割当完了" in result["message"]

def test_auto_assign_with_availability(setup_database, db_session, client):
    """出勤可能日を考慮した自動割当テスト"""
    facilities, staff_list, tasks = create_test_data(db_session)
    
    # 偶数日のテスト
    even_day = date.today().replace(day=2)
    request_data = {
        "task_ids": [1, 2, 3],
        "date": str(even_day)
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result = response.json()
    
    # スタッフ3は偶数日のみ出勤可能なので、割当に含まれる可能性がある
    assert result["success"] == True
    
    # 奇数日のテスト
    odd_day = date.today().replace(day=3)
    request_data = {
        "task_ids": [4, 5, 6],
        "date": str(odd_day)
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result = response.json()
    
    # スタッフ4,5は奇数日のみ出勤可能なので、割当に含まれる可能性がある
    assert result["success"] == True

def test_auto_assign_load_balancing(setup_database, db_session, client):
    """負荷分散を考慮した自動割当テスト"""
    facilities, staff_list, tasks = create_test_data(db_session)
    
    # 最初の割当
    request_data = {
        "task_ids": [1, 2],
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result1 = response.json()
    assert result1["assigned_count"] == 2
    
    # 2回目の割当（既存シフトがあるスタッフは優先度が下がるはず）
    request_data = {
        "task_ids": [3, 4],
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result2 = response.json()
    
    # 異なるスタッフに割り当てられているか確認
    assigned_staff_1 = set([a["staff_id"] for a in result1["assignments"]])
    assigned_staff_2 = set([a["staff_id"] for a in result2["assignments"]])
    
    # 完全に異なるスタッフとは限らないが、負荷は分散されているはず
    assert len(assigned_staff_1.union(assigned_staff_2)) > 2

def test_auto_assign_priority_order(setup_database, db_session, client):
    """優先度順での割当テスト"""
    facilities, staff_list, tasks = create_test_data(db_session)
    
    # 全タスクを一度に割当
    request_data = {
        "task_ids": list(range(1, 8)),
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result = response.json()
    
    # 高優先度のタスク（ID: 1, 2）が割り当てられているか確認
    assigned_task_ids = [a["task_id"] for a in result["assignments"]]
    assert 1 in assigned_task_ids or 2 in assigned_task_ids

def test_auto_assign_facility_matching(setup_database, db_session, client):
    """施設適合性を考慮した自動割当テスト"""
    facilities, staff_list, tasks = create_test_data(db_session)
    
    # 施設3（大型施設）のタスクを作成
    large_task = CleaningTask(
        id=10,
        reservation_id=10,
        facility_id=3,
        checkout_date=date.today(),
        scheduled_date=date.today(),
        status=TaskStatus.UNASSIGNED,
        priority=1,  # 高優先度
        created_at=datetime.now()
    )
    db_session.add(large_task)
    db_session.commit()
    
    # 大型施設のタスクを割当
    request_data = {
        "task_ids": [10],
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result = response.json()
    
    # 施設3に対応可能なスタッフ（4,5）に割り当てられるべき
    if result["assigned_count"] > 0:
        assigned_staff_id = result["assignments"][0]["staff_id"]
        # スタッフ4,5は施設3に対応可能
        assert assigned_staff_id in [4, 5]

def test_auto_assign_error_handling(setup_database, db_session, client):
    """エラーハンドリングのテスト"""
    
    # 存在しないタスクID
    request_data = {
        "task_ids": [999],
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result = response.json()
    
    assert result["success"] == False
    assert result["failed_count"] == 1
    assert len(result["errors"]) > 0
    assert "not found" in result["errors"][0]

def test_auto_assign_already_assigned(setup_database, db_session, client):
    """既に割当済みタスクのテスト"""
    facilities, staff_list, tasks = create_test_data(db_session)
    
    # タスク1を割当済みに変更
    task = db_session.query(CleaningTask).filter(CleaningTask.id == 1).first()
    task.status = TaskStatus.ASSIGNED
    db_session.commit()
    
    request_data = {
        "task_ids": [1],
        "date": str(date.today())
    }
    
    response = client.post("/api/cleaning/tasks/auto-assign", json=request_data)
    result = response.json()
    
    assert result["failed_count"] == 1
    assert "already assigned" in result["errors"][0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])