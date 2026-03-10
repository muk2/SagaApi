from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PastChampionBase(BaseModel):
    name: str
    year: int


class PastChampionCreate(PastChampionBase):
    pass


class PastChampionUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None


class PastChampionResponse(PastChampionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PastChampionPublic(BaseModel):
    """Public schema — only name and year"""
    id: int
    name: str
    year: int

    class Config:
        from_attributes = True