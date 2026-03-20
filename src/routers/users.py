import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from services.auth_service import get_membership_expiration, is_membership_expired
from services.paypal_service import capture_order, PayPalCaptureDeclined, PayPalError

logger = logging.getLogger(__name__)

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
    message, handicap, ghin_number = service.update_user_profile(current_user.id, data)
    return UserProfileUpdateResponse(message=message, handicap=handicap, ghin_number=ghin_number)


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


class RenewMembershipRequest(BaseModel):
    membership: str
    paypal_order_id: Optional[str] = None


class RenewMembershipResponse(BaseModel):
    message: str
    membership: str
    membership_expired: bool


@router.post("/renew-membership", response_model=RenewMembershipResponse)
async def renew_membership(
    data: RenewMembershipRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> RenewMembershipResponse:
    """Renew the current user's membership with payment."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Look up membership price
    from models.membership_option import MembershipOption
    membership_option = db.query(MembershipOption).filter(
        MembershipOption.name == data.membership,
        MembershipOption.is_active == True,
    ).first()

    if not membership_option:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Membership type '{data.membership}' not found",
        )

    amount = float(membership_option.price)

    # Process PayPal payment if required (paid tiers)
    if data.paypal_order_id:
        try:
            capture = await capture_order(data.paypal_order_id)
            logger.info(
                "Membership renewal payment captured for user %s: capture_id=%s amount=%s",
                user.id, capture.capture_id, amount,
            )
        except PayPalCaptureDeclined as e:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(e) or "Payment was declined. Please try again.",
            )
        except PayPalError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e) or "Payment processing failed. Please try again.",
            )
    elif amount > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment required for this membership tier",
        )

    # Update membership and expiration
    user.membership = data.membership
    user.membership_expires_at = get_membership_expiration()
    db.commit()

    # Send confirmation email
    try:
        from services.email_service import EmailService
        from repositories.auth_repository import AuthRepository
        repo = AuthRepository(db)
        account = repo.get_user_account_by_user_id(user.id)
        if account:
            EmailService().send_membership_confirmation_email(
                to_email=account.email,
                member_name=f"{user.first_name} {user.last_name}",
                membership_type=user.membership,
                price=amount,
            )
    except Exception:
        logger.exception("Failed to send renewal email for user_id=%s", user.id)

    return RenewMembershipResponse(
        message="Membership renewed successfully",
        membership=user.membership,
        membership_expired=False,
    )