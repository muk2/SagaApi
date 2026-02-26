# ===================================================================
# File: schemas/faq.py
# FAQ Pydantic Schemas
# ===================================================================

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FAQBase(BaseModel):
    question: str
    answer: str
    display_order: int = 0
    is_active: bool = True

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class FAQResponse(FAQBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FAQPublic(BaseModel):
    """Public FAQ schema (no timestamps, only active FAQs)"""
    id: int
    question: str
    answer: str
    display_order: int

    class Config:
        from_attributes = True