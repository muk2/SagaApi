from datetime import datetime

from pydantic import BaseModel


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile (handicap)."""

    handicap: int | None = None


class UserProfileUpdateResponse(BaseModel):
    """Response schema for profile update."""

    message: str
    handicap: int | None = None


class PasswordResetRequest(BaseModel):
    """Request schema for password reset."""

    current_password: str
    new_password: str


class PasswordResetResponse(BaseModel):
    """Response schema for password reset."""

    message: str


class EventRegistrationResponse(BaseModel):
    """Response schema for a single event registration."""

    id: int
    event_id: int
    township: str
    golf_course: str
    registered_at: datetime
    status: str

    model_config = {"from_attributes": True}


class UserEventsResponse(BaseModel):
    """Response schema for user's registered events."""

    events: list[EventRegistrationResponse]


class EventRegistrationRequest(BaseModel):
    """Request schema for registering for an event."""

    event_id: int


class EventRegistrationCreateResponse(BaseModel):
    """Response schema for creating an event registration."""

    message: str
    registration: EventRegistrationResponse
