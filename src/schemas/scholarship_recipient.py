from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScholarshipRecipientBase(BaseModel):
    full_name: str
    year: int
    bio: Optional[str] = None
    display_order: int = 0

class ScholarshipRecipientCreate(ScholarshipRecipientBase):
    pass

class ScholarshipRecipientUpdate(BaseModel):
    full_name: Optional[str] = None
    year: Optional[int] = None
    display_order: Optional[int] = None

class ScholarshipRecipientResponse(ScholarshipRecipientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScholarshipRecipientPublic(BaseModel):
    """Public schema for displaying recipients"""
    id: int
    full_name: str
    year: int

    class Config:
        from_attributes = True