from datetime import date as dt_date
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from pydantic import field_serializer


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile (handicap)."""

    handicap: Optional[str] = None


class UserProfileUpdateResponse(BaseModel):
    """Response schema for profile update."""

    message: str
    handicap: Optional[str] = None


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
    date: dt_date
    state: str
  

    model_config = {"from_attributes": True}

    @field_serializer('date')
    def serialize_date(self, date_val: dt_date, _info):
        return date_val.strftime("%m/%d/%Y") 

class UserEventsResponse(BaseModel):
    """Response schema for user's registered events."""

    events: List[EventRegistrationResponse]


class EventRegistrationRequest(BaseModel):
    """Request schema for registering for an event."""

    event_id: int
    email: EmailStr
    phone: str
    handicap: Optional[str] = None

class EventRegistrationCreateResponse(BaseModel):
    """Response schema for creating an event registration."""

    message: str
    registration: EventRegistrationResponse
