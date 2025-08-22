"""
清掃タスク自動生成のエラーハンドリングテスト
"""
import pytest
from datetime import date, time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.database import Base
from api.models.property import Facility
from api.models.reservation import Reservation
from api.models.cleaning import CleaningTask as CleaningTaskModel, TaskStatus
from api.crud import cleaning as crud


# テスト用データベース設定
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def test_auto_create_with_no_reservations(test_db):
    """予約がない場合のテスト"""
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 1))
    
    assert result.created_tasks == []
    assert result.stats['total_reservations'] == 0
    assert result.stats['created_tasks'] == 0
    assert result.stats['errors'] == 0
    assert len(result.errors) == 0


def test_auto_create_with_empty_room_type(test_db):
    """room_typeが空の場合のテスト"""
    reservation = Reservation(
        reservation_id="r1",
        reservation_type="予約",
        reservation_number="123",
        room_type="",  # 空文字
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # エラーが発生するはず
    assert result.stats['errors'] == 1
    assert len(result.errors) == 1
    assert "Room type is empty" in result.errors[0]['error']


def test_auto_create_with_whitespace_room_type(test_db):
    """room_typeが空白のみの場合のテスト"""
    reservation = Reservation(
        reservation_id="r1",
        reservation_type="予約",
        reservation_number="123",
        room_type="   ",  # 空白のみ
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # エラーが発生するはず
    assert result.stats['errors'] == 1
    assert len(result.errors) == 1
    assert "Room type is empty" in result.errors[0]['error']


def test_auto_create_creates_default_facility_when_no_facilities_exist(test_db):
    """施設が存在しない場合にデフォルト施設が作成されるテスト"""
    reservation = Reservation(
        reservation_id="r1",
        reservation_type="予約", 
        reservation_number="123",
        room_type=None,  # room_typeなし
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # デフォルト施設が作成され、タスクも作成されるはず
    assert result.stats['created_facilities'] == 1
    assert result.stats['created_tasks'] == 1
    assert len(result.warnings) == 1
    assert "Created default facility" in result.warnings[0]['warning']
    
    # 確認
    facility = test_db.query(Facility).first()
    assert facility.name == "デフォルト施設"


def test_auto_create_uses_existing_default_facility(test_db):
    """既存のデフォルト施設を使用するテスト"""
    # 既存施設を作成
    existing_facility = Facility(name="既存施設", is_active=True)
    test_db.add(existing_facility)
    test_db.commit()
    
    reservation = Reservation(
        reservation_id="r1",
        reservation_type="予約",
        reservation_number="123", 
        room_type=None,  # room_typeなし
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # 既存施設を使用し、タスクが作成されるはず
    assert result.stats['created_facilities'] == 0  # 新規作成なし
    assert result.stats['created_tasks'] == 1
    assert len(result.warnings) == 1
    assert "Used default facility due to missing room_type" in result.warnings[0]['warning']
    
    # 予約のfacility_idが更新されているはず
    test_db.refresh(reservation)
    assert reservation.facility_id == existing_facility.id


def test_auto_create_facility_creation_from_room_type(test_db):
    """room_typeから新しい施設が作成されるテスト"""
    reservation = Reservation(
        reservation_id="r1",
        reservation_type="予約",
        reservation_number="123",
        room_type="テスト施設A",
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # 新しい施設とタスクが作成されるはず
    assert result.stats['created_facilities'] == 1
    assert result.stats['created_tasks'] == 1
    assert result.stats['errors'] == 0
    
    # 施設が作成されているか確認
    facility = test_db.query(Facility).filter_by(name="テスト施設A").first()
    assert facility is not None
    assert facility.is_active is True
    
    # 予約のfacility_idが更新されているか確認
    test_db.refresh(reservation)
    assert reservation.facility_id == facility.id


def test_auto_create_uses_existing_facility_from_room_type(test_db):
    """room_typeから既存施設を使用するテスト"""
    # 既存施設を作成
    existing_facility = Facility(name="既存施設", is_active=True)
    test_db.add(existing_facility)
    test_db.commit()
    
    reservation = Reservation(
        reservation_id="r1", 
        reservation_type="予約",
        reservation_number="123",
        room_type="既存施設",  # 既存施設と同じ名前
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # 既存施設を使用し、タスクが作成されるはず
    assert result.stats['created_facilities'] == 0  # 新規作成なし
    assert result.stats['created_tasks'] == 1
    assert result.stats['errors'] == 0
    
    # 予約のfacility_idが更新されているか確認
    test_db.refresh(reservation)
    assert reservation.facility_id == existing_facility.id


def test_auto_create_skips_cancelled_reservations(test_db):
    """キャンセル予約をスキップするテスト"""
    reservation = Reservation(
        reservation_id="r1",
        reservation_type="キャンセル",  # キャンセル予約
        reservation_number="123",
        room_type="テスト施設",
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    test_db.add(reservation)
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # キャンセル予約は処理されないはず
    assert result.stats['total_reservations'] == 0
    assert result.stats['created_tasks'] == 0
    assert result.stats['created_facilities'] == 0


def test_auto_create_multiple_reservations_mixed_scenarios(test_db):
    """複数予約の混合シナリオテスト"""
    # 既存施設
    existing_facility = Facility(name="既存施設", is_active=True)
    test_db.add(existing_facility)
    test_db.flush()
    
    # 予約1: 正常ケース（新しい施設作成）
    reservation1 = Reservation(
        reservation_id="r1",
        reservation_type="予約",
        reservation_number="123",
        room_type="新施設A",
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    
    # 予約2: room_typeが空白（エラーケース）
    reservation2 = Reservation(
        reservation_id="r2",
        reservation_type="予約",
        reservation_number="456",
        room_type="",
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    
    # 予約3: 既存施設使用（正常ケース）
    reservation3 = Reservation(
        reservation_id="r3",
        reservation_type="予約",
        reservation_number="789",
        room_type="既存施設",
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    
    test_db.add_all([reservation1, reservation2, reservation3])
    test_db.commit()
    
    result = crud.auto_create_cleaning_tasks(test_db, date(2024, 1, 2))
    
    # 結果確認
    assert result.stats['total_reservations'] == 3
    assert result.stats['created_tasks'] == 2  # reservation1, reservation3
    assert result.stats['created_facilities'] == 1  # 新施設A
    assert result.stats['errors'] == 1  # reservation2のエラー
    assert len(result.errors) == 1
    assert result.errors[0]['reservation_id'] == reservation2.id