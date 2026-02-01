from fastapi import APIRouter, Depends, HTTPException
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
    """Register the current user for an event."""
    service = UserService(db)
    
    # Get the user_account_id from the user
    user_account = service.repo.get_user_account_by_user_id(current_user.id)
    if not user_account:
        raise HTTPException(status_code=404, detail="User account not found")
    
    registration = service.register_for_event(
        user_account_id=user_account.id,  
        event_id=data.event_id,
        email=data.email,
        phone=data.phone,
        handicap=data.handicap
    )
    return EventRegistrationCreateResponse(
        message="Successfully registered for event", registration=registration
    )
