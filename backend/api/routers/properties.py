from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas import Facility, FacilityCreate
from ..crud import get_facilities, get_facility, create_facility

router = APIRouter(
    prefix="/api/properties",
    tags=["施設管理"],
    responses={404: {"description": "Not found"}}
)

@router.get(
    "",
    response_model=List[Facility],
    summary="施設一覧の取得",
    description="登録されている全施設の一覧を取得します"
)
def list_facilities(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    db: Session = Depends(get_db)
):
    """
    施設一覧を取得
    
    ### 取得できる情報:
    - 施設ID、名称
    - 施設グループ
    - 住所、最大収容人数
    - アクティブ状態
    """
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