from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import CurrentUser
from schemas.user import (
    EventRegistrationCreateResponse,
    EventRegistrationRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    UserEventsResponse,
    UserProfileUpdateRequest,
    UserProfileUpdateResponse,
)
from services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/events", response_model=UserEventsResponse)
def get_user_events(
    current_user: CurrentUser, db: Session = Depends(get_db)
) -> UserEventsResponse:
    """
    Get all events the current user is registered for.

    Returns a list of events with registration details.
    Requires authentication.
    """
    service = UserService(db)
    events = service.get_user_events(current_user.id)
    return UserEventsResponse(events=events)


@router.put("/profile", response_model=UserProfileUpdateResponse)
def update_user_profile(
    data: UserProfileUpdateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> UserProfileUpdateResponse:
    """
    Update the current user's profile.

    Currently supports updating handicap.
    Requires authentication.
    """
    service = UserService(db)
    message, handicap = service.update_user_profile(current_user.id, data)
    return UserProfileUpdateResponse(message=message, handicap=handicap)


@router.put("/password", response_model=PasswordResetResponse)
def reset_password(
    data: PasswordResetRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    """
    Reset the current user's password.

    Requires current password for verification.
    Requires authentication.
    """
    service = UserService(db)
    message = service.reset_password(current_user.id, data)
    return PasswordResetResponse(message=message)


@router.post("/event-registrations", response_model=EventRegistrationCreateResponse)
def register_for_event(
    data: EventRegistrationRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> EventRegistrationCreateResponse:
    """
    Register the current user for an event.

    Creates a new event registration linking the user to the specified event.
    Prevents duplicate registrations.
    Requires authentication.
    """
    service = UserService(db)
    registration = service.register_for_event(current_user.id, data.event_id)
    return EventRegistrationCreateResponse(
        message="Successfully registered for event", registration=registration
    )
