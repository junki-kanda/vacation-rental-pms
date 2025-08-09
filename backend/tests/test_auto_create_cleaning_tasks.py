from datetime import date, time
from pathlib import Path
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.database import Base
from api.models.property import Facility
from api.models.reservation import Reservation
from api.models.cleaning import CleaningTask as CleaningTaskModel, TaskStatus
from api.crud import cleaning as crud


def test_auto_create_cleaning_tasks_commits_without_tasks():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    existing_facility = Facility(name="Existing Facility", is_active=True)
    db.add(existing_facility)
    db.commit()
    db.refresh(existing_facility)

    reservation = Reservation(
        reservation_id="r1",
        reservation_type="予約",
        reservation_number="123",
        room_type="New Facility",
        check_in_date=date(2024, 1, 1),
        check_out_date=date(2024, 1, 2),
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    existing_task = CleaningTaskModel(
        reservation_id=reservation.id,
        facility_id=existing_facility.id,
        checkout_date=reservation.check_out_date,
        checkout_time=time(10, 0),
        scheduled_date=reservation.check_out_date,
        scheduled_start_time=time(11, 0),
        scheduled_end_time=time(13, 0),
        estimated_duration_minutes=120,
        priority=3,
        status=TaskStatus.UNASSIGNED,
    )
    db.add(existing_task)
    db.commit()

    created = crud.auto_create_cleaning_tasks(db, reservation.check_out_date)
    assert created == []
    reservation_id = reservation.id

    db.close()

    new_session = TestingSessionLocal()
    new_facility = new_session.query(Facility).filter_by(name="New Facility").first()
    assert new_facility is not None
    updated_reservation = new_session.query(Reservation).filter_by(id=reservation_id).first()
    assert updated_reservation.facility_id == new_facility.id
    new_session.close()
