from sqlalchemy.orm import Session
from ..models import Facility
from ..schemas import FacilityCreate

def get_facility(db: Session, facility_id: int):
    return db.query(Facility).filter(Facility.id == facility_id).first()

def get_facility_by_name(db: Session, name: str):
    return db.query(Facility).filter(Facility.name == name).first()

def get_facilities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Facility).offset(skip).limit(limit).all()

def create_facility(db: Session, facility: FacilityCreate):
    db_facility = Facility(**facility.dict())
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility

def get_or_create_facility(db: Session, name: str, room_type_identifier: str):
    facility = get_facility_by_name(db, name)
    if not facility:
        facility = create_facility(
            db,
            FacilityCreate(
                name=name,
                room_type_identifier=room_type_identifier
            )
        )
    return facility