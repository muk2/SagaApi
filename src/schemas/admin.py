from datetime import date as dt_date
from datetime import time as dt_time
from decimal import Decimal

from pydantic import BaseModel, field_serializer

# ── User Schemas ──────────────────────────────────────────────────────────────


class AdminUserResponse(BaseModel):
    """Response schema for a user in the admin panel."""

    id: int
    first_name: str
    last_name: str
    phone_number: str | None = None
    handicap: str | None = None
    email: str | None = None
    role: str | None = None

    model_config = {"from_attributes": True}


class AdminUserListResponse(BaseModel):
    """Response schema for listing all users."""

    users: list[AdminUserResponse]


class UpdateUserRoleRequest(BaseModel):
    """Request schema for updating a user's role."""

    role: str


class UpdateUserRoleResponse(BaseModel):
    """Response schema for updating a user's role."""

    message: str
    user: AdminUserResponse


class DeleteUserResponse(BaseModel):
    """Response schema for deleting a user."""

    message: str


# ── Event Schemas ─────────────────────────────────────────────────────────────


class CreateEventRequest(BaseModel):
    """Request schema for creating an event."""

    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: dt_time


class AdminEventResponse(BaseModel):
    """Response schema for an event in the admin panel."""

    id: int
    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: dt_time

    model_config = {"from_attributes": True}

    @field_serializer("date")
    def serialize_date(self, date_val: dt_date, _info):
        return date_val.strftime("%m/%d/%Y")


class CreateEventResponse(BaseModel):
    """Response schema for creating an event."""

    message: str
    event: AdminEventResponse


class UpdateEventRequest(BaseModel):
    """Request schema for updating an event."""

    township: str | None = None
    state: str | None = None
    zipcode: str | None = None
    golf_course: str | None = None
    date: dt_date | None = None
    start_time: dt_time | None = None


class UpdateEventResponse(BaseModel):
    """Response schema for updating an event."""

    message: str
    event: AdminEventResponse


class DeleteEventResponse(BaseModel):
    """Response schema for deleting an event."""

    message: str


class EventRegistrationDetailResponse(BaseModel):
    """Response schema for a single event registration (admin view)."""

    id: int
    event_id: int
    user_id: int | None = None
    guest_id: int | None = None
    handicap: str | None = None
    email: str | None = None
    phone: str | None = None
    payment_status: str
    payment_method: str | None = None
    amount_paid: Decimal | None = None

    model_config = {"from_attributes": True}


class EventRegistrationsListResponse(BaseModel):
    """Response schema for listing registrations for an event."""

    event_id: int
    registrations: list[EventRegistrationDetailResponse]


# ── Banner Schemas ────────────────────────────────────────────────────────────


class BannerMessageItem(BaseModel):
    """Schema for a single banner message."""

    message: str


class UpdateBannerMessagesRequest(BaseModel):
    """Request schema for replacing all banner messages."""

    messages: list[BannerMessageItem]


class BannerMessageResponse(BaseModel):
    """Response schema for a single banner message."""

    id: int
    message: str

    model_config = {"from_attributes": True}


class UpdateBannerMessagesResponse(BaseModel):
    """Response schema for updating banner messages."""

    message: str
    banners: list[BannerMessageResponse]
