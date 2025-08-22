"""清掃タスクのグループ一括割当機能のテスト"""

import pytest
from datetime import date, datetime, time, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.database import Base, get_db
from api.main import app
from api.models.cleaning import (
    Staff, StaffGroup, StaffGroupMember,
    CleaningTask, CleaningShift, TaskStatus, ShiftStatus
)
from api.models.property import Facility
from api.models.reservation import Reservation
from api.schemas.staff_group import GroupAssignment

# テスト用データベース設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_group_assign.db"
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
    # テストごとにデータをクリア
    session.query(CleaningShift).delete()
    session.query(StaffGroupMember).delete()
    session.query(CleaningTask).delete()
    session.query(StaffGroup).delete()
    session.query(Staff).delete()
    session.query(Reservation).delete()
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
            max_guests=4
        )
        db_session.add(facility)
        facilities.append(facility)
    
    # スタッフグループを作成
    group1 = StaffGroup(
        id=1,
        name="清掃チームA",
        description="ベテランチーム",
        can_handle_large_properties=True,
        rate_per_property=8000,
        rate_per_property_with_option=9000,
        transportation_fee=1000,
        is_active=True
    )
    db_session.add(group1)
    
    group2 = StaffGroup(
        id=2,
        name="清掃チームB",
        description="通常チーム",
        can_handle_large_properties=False,
        rate_per_property=6000,
        rate_per_property_with_option=7000,
        transportation_fee=500,
        is_active=True
    )
    db_session.add(group2)
    
    # スタッフを作成
    staff_list = []
    for i in range(1, 6):
        staff = Staff(
            id=i,
            name=f"スタッフ{i}",
            email=f"staff{i}@example.com",
            phone=f"090-0000-000{i}",
            is_active=True,
            available_facilities=[1, 2] if i <= 3 else [2, 3]
        )
        db_session.add(staff)
        staff_list.append(staff)
    
    # グループメンバーを設定
    # グループ1（チームA）: スタッフ1,2,3
    for i in [1, 2, 3]:
        member = StaffGroupMember(
            group_id=1,
            staff_id=i,
            role="メンバー" if i > 1 else "リーダー",
            is_leader=(i == 1),
            joined_date=date.today()
        )
        db_session.add(member)
    
    # グループ2（チームB）: スタッフ4,5
    for i in [4, 5]:
        member = StaffGroupMember(
            group_id=2,
            staff_id=i,
            role="メンバー" if i > 4 else "リーダー",
            is_leader=(i == 4),
            joined_date=date.today()
        )
        db_session.add(member)
    
    # 予約を作成
    reservations = []
    for i in range(1, 6):
        reservation = Reservation(
            id=i,
            reservation_id=f"RES00{i}",
            reservation_number=f"R00{i}",
            facility_id=(i % 3) + 1,
            guest_name=f"ゲスト{i}",
            check_in_date=date.today() + timedelta(days=i),
            check_out_date=date.today() + timedelta(days=i+1),
            num_adults=2,
            num_children=0,
            num_infants=0,
            total_amount=50000,
            ota_name="一休",
            reservation_type="予約"
        )
        db_session.add(reservation)
        reservations.append(reservation)
    
    # 清掃タスクを作成
    tasks = []
    for i in range(1, 6):
        task = CleaningTask(
            id=i,
            reservation_id=i,
            facility_id=(i % 3) + 1,
            checkout_date=date.today() + timedelta(days=i),
            scheduled_date=date.today() + timedelta(days=i),
            status=TaskStatus.UNASSIGNED,
            priority=1 if i <= 2 else 3,
            estimated_duration_minutes=300,
            created_at=datetime.now()
        )
        db_session.add(task)
        tasks.append(task)
    
    db_session.commit()
    return {
        "facilities": facilities,
        "groups": [group1, group2],
        "staff": staff_list,
        "reservations": reservations,
        "tasks": tasks
    }

def test_group_assign_single_task(setup_database, db_session, client):
    """グループの単一タスク割当テスト"""
    data = create_test_data(db_session)
    
    # グループ1にタスク1を割当
    request_data = {
        "task_ids": [1],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00",
        "notes": "テスト割当"
    }
    
    response = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    assert result["assigned_count"] == 1
    assert len(result["shifts"]) == 1
    
    # データベースで確認
    shift = db_session.query(CleaningShift).filter(
        CleaningShift.task_id == 1
    ).first()
    assert shift is not None
    assert shift.group_id == 1
    assert shift.staff_id is None  # グループ割当なのでstaff_idはNULL
    assert shift.status == ShiftStatus.SCHEDULED

def test_group_assign_multiple_tasks(setup_database, db_session, client):
    """グループの複数タスク一括割当テスト"""
    data = create_test_data(db_session)
    
    # グループ1に複数タスクを一括割当
    request_data = {
        "task_ids": [1, 2, 3],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00",
        "notes": "一括割当テスト"
    }
    
    response = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    assert result["assigned_count"] == 3
    assert len(result["shifts"]) == 3
    
    # 各タスクが割り当てられたか確認
    for task_id in [1, 2, 3]:
        shift = db_session.query(CleaningShift).filter(
            CleaningShift.task_id == task_id
        ).first()
        assert shift is not None
        assert shift.group_id == 1
        
        # タスクのステータスが更新されたか確認
        task = db_session.query(CleaningTask).filter(
            CleaningTask.id == task_id
        ).first()
        assert task.status == TaskStatus.ASSIGNED

def test_group_assign_duplicate_prevention(setup_database, db_session, client):
    """重複割当防止のテスト"""
    data = create_test_data(db_session)
    
    # 最初の割当
    request_data = {
        "task_ids": [1],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response1 = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    assert response1.status_code == 200
    
    # 同じタスクに再度割当を試みる
    response2 = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    
    assert response2.status_code == 200
    result2 = response2.json()
    assert result2["assigned_count"] == 0  # 既に割当済みなので0件

def test_group_assign_different_groups(setup_database, db_session, client):
    """異なるグループへの割当テスト"""
    data = create_test_data(db_session)
    
    # グループ1にタスク1,2を割当
    request_data1 = {
        "task_ids": [1, 2],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response1 = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data1
    )
    assert response1.status_code == 200
    assert response1.json()["assigned_count"] == 2
    
    # グループ2にタスク3,4を割当
    request_data2 = {
        "task_ids": [3, 4],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "11:00",
        "scheduled_end_time": "16:00"
    }
    
    response2 = client.post(
        "/api/staff-groups/2/assign-tasks",
        json=request_data2
    )
    assert response2.status_code == 200
    assert response2.json()["assigned_count"] == 2
    
    # 各グループのシフトを確認
    group1_shifts = db_session.query(CleaningShift).filter(
        CleaningShift.group_id == 1
    ).all()
    assert len(group1_shifts) == 2
    
    group2_shifts = db_session.query(CleaningShift).filter(
        CleaningShift.group_id == 2
    ).all()
    assert len(group2_shifts) == 2

def test_group_unassign_task(setup_database, db_session, client):
    """グループのタスク割当解除テスト"""
    data = create_test_data(db_session)
    
    # まず割当を行う
    request_data = {
        "task_ids": [1],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    assert response.status_code == 200
    
    # 割当解除
    response = client.delete("/api/staff-groups/1/tasks/1")
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]
    
    # シフトが削除されたか確認
    shift = db_session.query(CleaningShift).filter(
        CleaningShift.task_id == 1,
        CleaningShift.group_id == 1
    ).first()
    assert shift is None
    
    # タスクのステータスが未割当に戻ったか確認
    task = db_session.query(CleaningTask).filter(
        CleaningTask.id == 1
    ).first()
    assert task.status == TaskStatus.UNASSIGNED

def test_get_group_shifts(setup_database, db_session, client):
    """グループのシフト取得テスト"""
    data = create_test_data(db_session)
    
    # 複数タスクを割当
    request_data = {
        "task_ids": [1, 2, 3],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    assert response.status_code == 200
    
    # グループのシフトを取得
    response = client.get("/api/staff-groups/1/shifts")
    assert response.status_code == 200
    
    shifts = response.json()
    assert len(shifts) == 3
    
    # 各シフトの情報を確認
    for shift in shifts:
        assert shift["task_id"] in [1, 2, 3]
        assert shift["scheduled_start_time"] is not None
        assert shift["scheduled_end_time"] is not None
        assert shift["task"] is not None

def test_group_shifts_with_date_filter(setup_database, db_session, client):
    """日付フィルタ付きグループシフト取得テスト"""
    data = create_test_data(db_session)
    
    # 異なる日付でタスクを割当
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # 今日のタスク
    request_data1 = {
        "task_ids": [1],
        "assigned_date": str(today),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response1 = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data1
    )
    assert response1.status_code == 200
    
    # 明日のタスク
    request_data2 = {
        "task_ids": [2],
        "assigned_date": str(tomorrow),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response2 = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data2
    )
    assert response2.status_code == 200
    
    # 今日のシフトのみ取得
    response = client.get(
        f"/api/staff-groups/1/shifts?start_date={today}&end_date={today}"
    )
    assert response.status_code == 200
    
    shifts = response.json()
    assert len(shifts) == 1
    assert shifts[0]["task_id"] == 1

def test_group_wage_calculation(setup_database, db_session, client):
    """グループ報酬計算のテスト"""
    data = create_test_data(db_session)
    
    # グループ1（報酬8000円、交通費1000円）にタスクを割当
    request_data = {
        "task_ids": [1],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    assert response.status_code == 200
    
    # データベースでシフトの報酬を確認
    shift = db_session.query(CleaningShift).filter(
        CleaningShift.task_id == 1
    ).first()
    
    assert shift.calculated_wage == 8000  # グループの基本報酬
    assert shift.transportation_fee == 1000  # グループの交通費
    assert shift.total_payment == 9000  # 合計

def test_invalid_group_id(setup_database, db_session, client):
    """無効なグループIDのテスト"""
    data = create_test_data(db_session)
    
    request_data = {
        "task_ids": [1],
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    # 存在しないグループID
    response = client.post(
        "/api/staff-groups/999/assign-tasks",
        json=request_data
    )
    assert response.status_code == 404

def test_invalid_task_ids(setup_database, db_session, client):
    """無効なタスクIDのテスト"""
    data = create_test_data(db_session)
    
    request_data = {
        "task_ids": [999, 1000],  # 存在しないタスクID
        "assigned_date": str(date.today()),
        "scheduled_start_time": "10:00",
        "scheduled_end_time": "15:00"
    }
    
    response = client.post(
        "/api/staff-groups/1/assign-tasks",
        json=request_data
    )
    assert response.status_code == 200
    result = response.json()
    assert result["assigned_count"] == 0  # 存在しないタスクなので0件

if __name__ == "__main__":
    pytest.main([__file__, "-v"])