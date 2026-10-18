from pydantic import BaseModel
from typing import Optional, List


class NewsItemBase(BaseModel):
    title: str
    url: str
    site_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0


class NewsItemCreate(NewsItemBase):
    pass


class NewsItemUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    site_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class NewsItemResponse(BaseModel):
    id: int
    title: str
    url: str
    site_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    display_order: int

    class Config:
        from_attributes = True


class NewsItemListResponse(BaseModel):
    news_items: List[NewsItemResponse]


class FetchNewsMetadataRequest(BaseModel):
    url: str


class FetchNewsMetadataResponse(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    site_name: Optional[str] = None
