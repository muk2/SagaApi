from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import CurrentUser
from models.user import User, UserAccount
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


class MemberSearchResult(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    handicap: Optional[str] = None


@router.get("/members/search", response_model=List[MemberSearchResult])
def search_members(
    current_user: CurrentUser,
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Search members by name. Requires authentication."""
    search = f"%{q.strip()}%"
    results = (
        db.query(User, UserAccount)
        .join(UserAccount, UserAccount.user_id == User.id)
        .filter(
            (User.first_name.ilike(search))
            | (User.last_name.ilike(search))
            | ((User.first_name + " " + User.last_name).ilike(search))
        )
        .limit(10)
        .all()
    )
    return [
        MemberSearchResult(
            user_id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            email=ua.email,
            phone=u.phone_number,
            handicap=u.handicap,
        )
        for u, ua in results
    ]


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

    user_account = service.repo.get_user_account_by_user_id(current_user.id)
    if not user_account:
        raise HTTPException(status_code=404, detail="User account not found")

    registration = service.register_for_event(
        user_account_id=user_account.id,
        event_id=data.event_id,
        email=data.email,
        phone=data.phone,
        handicap=data.handicap,
        is_sponsor=data.is_sponsor,
        sponsor_amount=data.sponsor_amount,
        company_name=data.company_name,
    )
    return EventRegistrationCreateResponse(
        message="Successfully registered for event", registration=registration
    )