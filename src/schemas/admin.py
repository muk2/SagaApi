from datetime import date as dt_date
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field, field_serializer


# Admin Users Schemas
class UserListItem(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: Optional[str] = None
    phone_number: Optional[str] = None
    handicap: Optional[str] = None
    membership: str
    last_logged_in: Optional[datetime] = None
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: List[UserListItem]


class UpdateUserRoleRequest(BaseModel):
    role: str


class UpdateUserRoleResponse(BaseModel):
    message: str
    user_id: int
    new_role: str


class DeleteUserResponse(BaseModel):
    message: str


class EventRegistrationDetail(BaseModel):
    id: int
    user_id: Optional[int] = None
    guest_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    handicap: Optional[str] = None
    payment_status: str
    payment_method: Optional[str] = None
    amount_paid: Optional[float] = None
    created_at: datetime
    user_name: Optional[str] = None
    membership: str = "guest"
    is_sponsor: bool = False
    sponsor_amount: Optional[float] = None
    company_name: Optional[str] = None
    model_config = {"from_attributes": True}


class EventRegistrationsResponse(BaseModel):
    event_id: int
    registrations: List[EventRegistrationDetail]


class CreateEventRequest(BaseModel):
    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: str
    member_price: float
    guest_price: float
    capacity: int
    image_url: Optional[str] = None


class UpdateEventRequest(BaseModel):
    township: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    golf_course: Optional[str] = None
    date: Optional[dt_date] = None
    start_time: Optional[str] = None
    member_price: Optional[float] = 0
    guest_price: Optional[float] = 0
    capacity: Optional[int] = 1
    image_url: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: str
    member_price: float
    guest_price: float
    capacity: int
    registered: int = 0
    image_url: Optional[str] = None
    model_config = {"from_attributes": True}

    @field_serializer("date")
    def serialize_date(self, date_val: dt_date, _info):
        return date_val.strftime("%m/%d/%Y")


class UpdateBannerMessagesRequest(BaseModel):
    messages: List[str]


class UpdateBannerSettingsRequest(BaseModel):
    display_count: int


class BannerResponse(BaseModel):
    message: str
    data: Optional[dict] = None


# ── Photo Albums ──────────────────────────────────────────────────
# Frontend sends/receives camelCase; SQLAlchemy model uses snake_case.
# Field aliases bridge the gap in both directions.

class PhotoAlbumCreate(BaseModel):
    """Accepts camelCase from the frontend; model_dump() returns snake_case for the ORM."""
    title: str
    date: dt_date
    cover_image: str = Field(alias="coverImage")
    google_drive_link: str = Field(alias="googleDriveLink")

    model_config = {"populate_by_name": True}


class PhotoAlbumUpdate(BaseModel):
    """Accepts camelCase from the frontend; model_dump() returns snake_case for the ORM."""
    title: Optional[str] = None
    date: Optional[dt_date] = None
    cover_image: Optional[str] = Field(default=None, alias="coverImage")
    google_drive_link: Optional[str] = Field(default=None, alias="googleDriveLink")

    model_config = {"populate_by_name": True}


class PhotoAlbumResponse(BaseModel):
    """Returns camelCase to the frontend, read from snake_case ORM attributes."""
    id: int
    title: str
    date: dt_date
    coverImage: str = Field(alias="cover_image", default="")
    googleDriveLink: str = Field(alias="google_drive_link", default="")

    model_config = {"from_attributes": True, "populate_by_name": True}


class PhotoAlbumListResponse(BaseModel):
    albums: List[PhotoAlbumResponse]


# ── Content ───────────────────────────────────────────────────────
class ContentItem(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class ContentResponse(BaseModel):
    content: List[ContentItem]


class UpdateContentRequest(BaseModel):
    content: Dict[str, str]


class MediaUploadResponse(BaseModel):
    message: str
    url: str


class CarouselImageItem(BaseModel):
    id: int
    image_url: str
    alt_text: Optional[str] = None
    display_order: int
    model_config = {"from_attributes": True}


class CarouselImagesResponse(BaseModel):
    images: List[str]


class UpdateCarouselImagesRequest(BaseModel):
    images: List[str]