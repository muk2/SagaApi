from datetime import date as dt_date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_serializer


# Admin Users Schemas
class UserListItem(BaseModel):
    """Schema for user in list view."""

    id: int
    first_name: str
    last_name: str
    email: str
    role: Optional[str] = None
    phone_number: Optional[str] = None
    handicap: Optional[str] = None
    last_logged_in: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Response schema for listing users."""

    users: list[UserListItem]


class UpdateUserRoleRequest(BaseModel):
    """Request schema for updating user role."""

    role: str


class UpdateUserRoleResponse(BaseModel):
    """Response schema for updating user role."""

    message: str
    user_id: int
    new_role: str


class DeleteUserResponse(BaseModel):
    """Response schema for deleting user."""

    message: str


class EventRegistrationDetail(BaseModel):
    """Schema for event registration details."""

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

    model_config = {"from_attributes": True}


class EventRegistrationsResponse(BaseModel):
    """Response schema for event registrations."""

    event_id: int
    registrations: list[EventRegistrationDetail]


# Admin Events Schemas
class CreateEventRequest(BaseModel):
    """Request schema for creating event."""

    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: str  # Format: "HH:MM:SS"


class UpdateEventRequest(BaseModel):
    """Request schema for updating event."""

    township: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    golf_course: Optional[str] = None
    date: Optional[dt_date] = None
    start_time: Optional[str] = None


class EventResponse(BaseModel):
    """Response schema for event operations."""

    id: int
    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: str

    model_config = {"from_attributes": True}

    @field_serializer("date")
    def serialize_date(self, date_val: dt_date, _info):
        return date_val.strftime("%m/%d/%Y")


# Admin Banner Schemas
class UpdateBannerMessagesRequest(BaseModel):
    """Request schema for updating banner messages."""

    messages: list[str]


class UpdateBannerSettingsRequest(BaseModel):
    """Request schema for updating banner display count."""

    display_count: int


class BannerResponse(BaseModel):
    """Response schema for banner operations."""

    message: str
    data: Optional[dict] = None


# Admin Photos Schemas
class PhotoAlbumCreate(BaseModel):
    """Request schema for creating photo album."""

    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    images: Optional[list[str]] = None


class PhotoAlbumUpdate(BaseModel):
    """Request schema for updating photo album."""

    title: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    images: Optional[list[str]] = None


class PhotoAlbumResponse(BaseModel):
    """Response schema for photo album."""

    id: int
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    images: Optional[list[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PhotoAlbumListResponse(BaseModel):
    """Response schema for listing photo albums."""

    albums: list[PhotoAlbumResponse]


# Admin Content Schemas
class ContentItem(BaseModel):
    """Schema for a single content item."""

    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class ContentResponse(BaseModel):
    """Response schema for site content."""

    content: list[ContentItem]


class UpdateContentRequest(BaseModel):
    """Request schema for updating content."""

    content: dict[str, str]  # key-value pairs


# Admin Media Schemas
class MediaUploadResponse(BaseModel):
    """Response schema for media upload."""

    message: str
    url: str


class CarouselImageItem(BaseModel):
    """Schema for carousel image."""

    id: int
    image_url: str
    alt_text: Optional[str] = None
    display_order: int

    model_config = {"from_attributes": True}


class CarouselImagesResponse(BaseModel):
    """Response schema for carousel images."""

    images: list[CarouselImageItem]


class UpdateCarouselImagesRequest(BaseModel):
    """Request schema for updating carousel images."""

    images: list[dict]  # [{image_url, alt_text, display_order}]
