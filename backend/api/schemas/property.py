from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Facility Schemas
class FacilityBase(BaseModel):
    name: str
    facility_group: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    cleaning_fee: Optional[float] = None
    base_rate: Optional[float] = None
    max_guests: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    is_active: Optional[bool] = True

class FacilityCreate(FacilityBase):
    pass

class Facility(FacilityBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True