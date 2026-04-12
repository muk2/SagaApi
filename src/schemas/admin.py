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
    ghin_number: Optional[str] = None
    membership: str
    membership_exempt: bool = False
    last_logged_in: Optional[datetime] = None
    created_at: Optional[datetime] = None
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


class CreateUserRequest(BaseModel):
    first_name:   str
    last_name:    str
    email:        EmailStr
    phone_number: str
    membership:   str
    role:         str = "user"
    handicap:     Optional[str] = None
    ghin_number:  Optional[str] = None
    membership_exempt: bool = False


class CreateUserResponse(BaseModel):
    id:           int
    first_name:   str
    last_name:    str
    email:        str
    phone_number: Optional[str] = None
    membership:   Optional[str] = None
    role:         Optional[str] = None
    handicap:     Optional[str] = None
    ghin_number:  Optional[str] = None


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
    event_type: str = "regular"


class UpdateEventRequest(BaseModel):
    township: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    golf_course: Optional[str] = None
    date: Optional[dt_date] = None
    start_time: Optional[str] = None
    member_price: Optional[float] = None
    guest_price: Optional[float] = None
    capacity: Optional[int] = None
    image_url: Optional[str] = None
    registration_open: Optional[bool] = None
    event_type: Optional[str] = None


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
    registration_open: bool = True
    event_type: str = "regular"
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


class PhotoAlbumCreate(BaseModel):
    title: str
    date: dt_date
    cover_image: str = Field(alias="coverImage")
    google_drive_link: str = Field(alias="googleDriveLink")
    model_config = {"populate_by_name": True}


class PhotoAlbumUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[dt_date] = None
    cover_image: Optional[str] = Field(default=None, alias="coverImage")
    google_drive_link: Optional[str] = Field(default=None, alias="googleDriveLink")
    model_config = {"populate_by_name": True}


class PhotoAlbumResponse(BaseModel):
    id: int
    title: str
    date: dt_date
    coverImage: str = Field(alias="cover_image", default="")
    googleDriveLink: str = Field(alias="google_drive_link", default="")
    model_config = {"from_attributes": True, "populate_by_name": True}


class PhotoAlbumListResponse(BaseModel):
    albums: List[PhotoAlbumResponse]


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


# Exemption Codes Schemas
class CreateExemptionCodeRequest(BaseModel):
    code: Optional[str] = None
    max_uses: int = 1
    expires_at: Optional[datetime] = None


class ExemptionCodeResponse(BaseModel):
    id: int
    code: str
    max_uses: int
    times_used: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ExemptionCodeListResponse(BaseModel):
    codes: List[ExemptionCodeResponse]


# Event Promo Codes Schemas
class CreateEventPromoCodeRequest(BaseModel):
    code: Optional[str] = None
    discount_type: str  # "member_price", "free", "percent"
    discount_value: Optional[float] = None  # required when discount_type == "percent"
    event_id: Optional[int] = None  # NULL = all events
    max_uses: int = 1
    expires_at: Optional[datetime] = None


class EventPromoCodeResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: Optional[float] = None
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    max_uses: int
    times_used: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class EventPromoCodeListResponse(BaseModel):
    codes: List[EventPromoCodeResponse]


class ValidateEventPromoCodeResponse(BaseModel):
    valid: bool
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    discounted_member_price: Optional[float] = None
    discounted_guest_price: Optional[float] = None
    message: Optional[str] = None