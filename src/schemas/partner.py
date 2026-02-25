from pydantic import BaseModel
from typing import Optional, List


class PartnerBase(BaseModel):
    name: str
    logo_url: str
    website_url: Optional[str] = None
    display_order: int = 0


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    display_order: Optional[int] = None


class PartnerResponse(BaseModel):
    id: int
    name: str
    logo_url: str
    website_url: Optional[str] = None
    display_order: int

    class Config:
        from_attributes = True


class PartnerListResponse(BaseModel):
    partners: List[PartnerResponse]