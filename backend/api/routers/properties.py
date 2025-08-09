from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import Facility, FacilityCreate
from ..crud import get_facilities, get_facility, create_facility

router = APIRouter(prefix="/api/properties", tags=["properties"])

@router.get("", response_model=List[Facility])
def list_facilities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """施設一覧を取得"""
    return get_facilities(db, skip=skip, limit=limit)

@router.get("/{facility_id}", response_model=Facility)
def get_facility_detail(facility_id: int, db: Session = Depends(get_db)):
    """施設詳細を取得"""
    facility = get_facility(db, facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@router.post("", response_model=Facility)
def create_new_facility(
    facility: FacilityCreate,
    db: Session = Depends(get_db)
):
    """施設を作成"""
    return create_facility(db, facility)