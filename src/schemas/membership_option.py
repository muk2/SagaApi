from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class MembershipOptionBase(BaseModel):
    name: str
    price: Decimal
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0

class MembershipOptionCreate(MembershipOptionBase):
    pass

class MembershipOptionUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class MembershipOptionResponse(MembershipOptionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MembershipOptionPublic(BaseModel):
    """Public schema for displaying membership options"""
    id: int
    name: str
    price: Decimal
    description: Optional[str]

    class Config:
        from_attributes = True