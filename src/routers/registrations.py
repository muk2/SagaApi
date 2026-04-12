from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import CurrentUser
from models.event import Event
from models.event_registration import EventRegistration
from models.guest import Guest
from models.user import User, UserAccount
from services.auth_service import is_membership_expired
from services.email_service import EmailService
from services.north_payment_service import (
    NorthDeclinedError,
    NorthGatewayError,
    charge_card,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/registrations", tags=["Registrations"])


# ── Schemas ─────────────────────────────────────────────────────────────────────

class AdditionalGolfer(BaseModel):
    """An additional golfer added by the registrant."""
    is_member:   bool = False
    user_id:     Optional[int]   = None   # set when is_member=True
    first_name:  Optional[str]   = None   # set when is_member=False (guest)
    last_name:   Optional[str]   = None
    email:       Optional[EmailStr] = None
    phone:       Optional[str]   = None
    handicap:    Optional[str]   = None


class MemberRegistrationRequest(BaseModel):
    event_id:           int
    payment_token:      Optional[str]   = None  # North tokenized card token
    handicap:           Optional[str]   = None
    is_sponsor:         bool            = False
    sponsor_amount:     Optional[float] = None
    company_name:       Optional[str]   = None
    additional_golfers: list[AdditionalGolfer] = []
    promo_code:         Optional[str]   = None


class GuestRegistrationRequest(BaseModel):
    event_id:           int
    payment_token:      Optional[str]   = None  # North tokenized card token
    first_name:         str
    last_name:          str
    email:              EmailStr
    phone:              str
    handicap:           Optional[str]   = None
    is_sponsor:         bool            = False
    sponsor_amount:     Optional[float] = None
    company_name:       Optional[str]   = None
    additional_golfers: list[AdditionalGolfer] = []
    promo_code:         Optional[str]   = None


class ValidatePromoCodeRequest(BaseModel):
    code:     str
    event_id: int


class RetryPaymentRequest(BaseModel):
    payment_token: str  # North tokenized card token


class RegistrationResponse(BaseModel):
    registration_id:  int
    confirmation_id:  str
    event_id:         int
    amount_charged:   float
    transaction_id:   Optional[str] = None
    card_last_four:   Optional[str] = None
    message:          str = "Registration confirmed"
    additional_ids:   list[int] = []


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_event_or_404(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


def _check_capacity(db: Session, event: Event, additional_spots: int = 1) -> None:
    registered = (
        db.query(EventRegistration)
        .filter(EventRegistration.event_id == event.id)
        .count()
    )
    if registered + additional_spots > event.capacity:
        remaining = event.capacity - registered
        if remaining <= 0:
            raise HTTPException(status_code=409, detail="This event is fully booked.")
        raise HTTPException(
            status_code=409,
            detail=f"Only {remaining} spot(s) remaining. Cannot register {additional_spots} golfer(s).",
        )



def _check_duplicate_member(db: Session, event_id: int, user_id: int) -> None:
    exists = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="You are already registered for this event.")


def _check_duplicate_guest(db: Session, event_id: int, email: str) -> None:
    exists = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_id == event_id,
            EventRegistration.email == email,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=409,
            detail="This email is already registered for this event.",
        )


def _confirmation_id(registration_id: int) -> str:
    return f"SAGA-{registration_id:06d}"


def _validate_promo_code(db: Session, code_str: str, event_id: int):
    """Validate a promo code and return the EventPromoCode object or raise HTTPException."""
    from models.event_promo_code import EventPromoCode
    from datetime import datetime, timezone

    promo = db.query(EventPromoCode).filter(EventPromoCode.code == code_str).first()
    if not promo:
        raise HTTPException(status_code=400, detail="Invalid promo code.")
    if not promo.is_active:
        raise HTTPException(status_code=400, detail="This promo code is no longer active.")
    if promo.times_used >= promo.max_uses:
        raise HTTPException(status_code=400, detail="This promo code has been fully used.")
    if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This promo code has expired.")
    if promo.event_id and promo.event_id != event_id:
        raise HTTPException(status_code=400, detail="This promo code is not valid for this event.")
    return promo


def _apply_promo_discount(promo, base_price: Decimal, member_price: Decimal) -> Decimal:
    """Apply promo discount and return the new price."""
    if promo.discount_type == "free":
        return Decimal("0")
    elif promo.discount_type == "member_price":
        return member_price
    elif promo.discount_type == "percent":
        discount = base_price * Decimal(str(promo.discount_value)) / Decimal("100")
        return max(base_price - discount, Decimal("0"))
    return base_price


# ── Validate promo code (public) ──────────────────────────────────────────────

@router.post("/validate-promo-code")
def validate_promo_code(
    data: ValidatePromoCodeRequest,
    db: Session = Depends(get_db),
):
    from models.event_promo_code import EventPromoCode
    from datetime import datetime, timezone

    promo = db.query(EventPromoCode).filter(EventPromoCode.code == data.code).first()
    if not promo:
        return {"valid": False, "message": "Invalid promo code."}
    if not promo.is_active:
        return {"valid": False, "message": "This promo code is no longer active."}
    if promo.times_used >= promo.max_uses:
        return {"valid": False, "message": "This promo code has been fully used."}
    if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
        return {"valid": False, "message": "This promo code has expired."}
    if promo.event_id and promo.event_id != data.event_id:
        return {"valid": False, "message": "This promo code is not valid for this event."}

    event = _get_event_or_404(db, data.event_id)
    member_price = Decimal(str(event.member_price or 0))
    guest_price = Decimal(str(event.guest_price or 0))

    return {
        "valid": True,
        "discount_type": promo.discount_type,
        "discount_value": float(promo.discount_value) if promo.discount_value else None,
        "discounted_member_price": float(_apply_promo_discount(promo, member_price, member_price)),
        "discounted_guest_price": float(_apply_promo_discount(promo, guest_price, member_price)),
    }


# ── Member registration ─────────────────────────────────────────────────────────

def _calculate_additional_golfer_price(
    db: Session, event: Event, golfer: "AdditionalGolfer",
) -> Decimal:
    """Return the price for one additional golfer (member rate or guest rate)."""
    if golfer.is_member and golfer.user_id:
        # Check if this member's membership is still active
        member = db.query(User).filter(User.id == golfer.user_id).first()
        if member and not is_membership_expired(member):
            return Decimal(str(event.member_price or event.guest_price))
    return Decimal(str(event.guest_price))


def _create_additional_registrations(
    db: Session, event: Event, golfers: list["AdditionalGolfer"],
    transaction_id: str | None, total_amount: float,
) -> list[int]:
    """Create EventRegistration rows for each additional golfer. Returns list of IDs."""
    additional_ids: list[int] = []
    for i, golfer in enumerate(golfers):
        if golfer.is_member and golfer.user_id:
            user = db.query(User).filter(User.id == golfer.user_id).first()
            ua = db.query(UserAccount).filter(UserAccount.user_id == golfer.user_id).first()
            reg = EventRegistration(
                event_id=event.id,
                user_id=ua.id if ua else None,
                email=ua.email if ua else None,
                phone=user.phone_number if user else None,
                handicap=golfer.handicap or (user.handicap if user else None),
                payment_status="paid",
                payment_method="north",
                amount_paid=float(_calculate_additional_golfer_price(db, event, golfer)),
                transaction_id=transaction_id,
            )
        else:
            guest = db.query(Guest).filter(Guest.email == golfer.email).first() if golfer.email else None
            if not guest and golfer.email:
                guest = Guest(
                    first_name=golfer.first_name or "",
                    last_name=golfer.last_name or "",
                    email=golfer.email,
                    phone=golfer.phone or "",
                )
                db.add(guest)
                db.flush()
            reg = EventRegistration(
                event_id=event.id,
                guest_id=guest.id if guest else None,
                email=golfer.email,
                phone=golfer.phone,
                handicap=golfer.handicap,
                payment_status="paid",
                payment_method="north",
                amount_paid=float(_calculate_additional_golfer_price(db, event, golfer)),
                transaction_id=transaction_id,
            )
        db.add(reg)
        db.flush()
        additional_ids.append(reg.id)
    return additional_ids


@router.post(
    "",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_member(
    data: MemberRegistrationRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> RegistrationResponse:
    """
    Register an authenticated member (+ optional additional golfers).
    Captures the PayPal order, then creates the registration records.
    """
    # Look up the user_account linked to this user
    user_account = db.query(UserAccount).filter(UserAccount.user_id == current_user.id).first()
    if not user_account:
        raise HTTPException(status_code=400, detail="No account found. Please complete your profile first.")

    event = _get_event_or_404(db, data.event_id)
    total_spots = 1 + len(data.additional_golfers)
    _check_capacity(db, event, total_spots)
    _check_duplicate_member(db, data.event_id, user_account.id)

    # Charge guest price if membership has expired
    registrant = db.query(User).filter(User.id == current_user.id).first()
    if registrant and not is_membership_expired(registrant):
        base = Decimal(str(event.member_price or event.guest_price))
    else:
        base = Decimal(str(event.guest_price))

    # Apply promo code discount
    promo = None
    if data.promo_code:
        promo = _validate_promo_code(db, data.promo_code, data.event_id)
        base = _apply_promo_discount(promo, base, Decimal(str(event.member_price or 0)))

    sponsor = Decimal(str(data.sponsor_amount or 0)) if data.is_sponsor else Decimal("0")
    total   = base + sponsor

    for golfer in data.additional_golfers:
        total += _calculate_additional_golfer_price(db, event, golfer)

    # Charge card via North (skip for free events)
    charge = None
    if data.payment_token:
        try:
            charge = await charge_card(data.payment_token, float(total))
        except NorthDeclinedError as exc:
            logger.warning("Member payment declined: user_id=%s event_id=%s", current_user.id, data.event_id)
            raise HTTPException(status_code=402, detail=str(exc))
        except NorthGatewayError as exc:
            logger.error("North error (member): %s", exc)
            raise HTTPException(status_code=502, detail=str(exc))

    registration = EventRegistration(
        event_id=data.event_id,
        user_id=user_account.id,
        email=user_account.email,
        phone=getattr(current_user, "phone_number", None),
        handicap=data.handicap,
        payment_status="paid" if charge else "free",
        payment_method="north" if charge else "none",
        amount_paid=float(base + sponsor),
        transaction_id=charge.transaction_id if charge else None,
        is_sponsor=data.is_sponsor,
        sponsor_amount=float(data.sponsor_amount) if data.is_sponsor and data.sponsor_amount else None,
        company_name=data.company_name if data.is_sponsor else None,
    )
    db.add(registration)
    db.flush()

    additional_ids = _create_additional_registrations(
        db, event, data.additional_golfers,
        charge.transaction_id if charge else None, float(total),
    )

    # Increment promo code usage
    if promo:
        promo.times_used += 1

    db.commit()
    db.refresh(registration)

    logger.info(
        "Member registered: registration_id=%s user_id=%s event_id=%s amount=%s additional=%d",
        registration.id, current_user.id, data.event_id, total, len(additional_ids),
    )

    # Send confirmation email
    try:
        registrant_name = f"{current_user.first_name} {current_user.last_name}"
        email_addr = user_account.email
        if email_addr:
            add_golfer_details = []
            for golfer in data.additional_golfers:
                price = float(_calculate_additional_golfer_price(db, event, golfer))
                if golfer.is_member and golfer.user_id:
                    u = db.query(User).filter(User.id == golfer.user_id).first()
                    name = f"{u.first_name} {u.last_name}" if u else "Member Golfer"
                else:
                    name = f"{golfer.first_name or ''} {golfer.last_name or ''}".strip() or "Guest Golfer"
                add_golfer_details.append({"name": name, "price": price})

            EmailService().send_event_registration_email(
                to_email=email_addr,
                registrant_name=registrant_name,
                event_name=event.golf_course,
                event_date=str(event.date),
                confirmation_id=_confirmation_id(registration.id),
                base_price=float(base + sponsor),
                additional_golfers=add_golfer_details if add_golfer_details else None,
                sponsor_amount=float(data.sponsor_amount) if data.is_sponsor and data.sponsor_amount else None,
                total=float(total),
            )
    except Exception:
        logger.exception("Failed to send event registration email for registration_id=%s", registration.id)

    return RegistrationResponse(
        registration_id=registration.id,
        confirmation_id=_confirmation_id(registration.id),
        event_id=data.event_id,
        amount_charged=float(total),
        transaction_id=charge.transaction_id if charge else None,
        additional_ids=additional_ids,
    )


# ── Guest registration ──────────────────────────────────────────────────────────

@router.post(
    "/guest",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_guest(
    data: GuestRegistrationRequest,
    db: Session = Depends(get_db),
) -> RegistrationResponse:
    """
    Register an unauthenticated guest (+ optional additional golfers).
    All additional golfers are charged at guest_price.
    """
    event = _get_event_or_404(db, data.event_id)
    total_spots = 1 + len(data.additional_golfers)
    _check_capacity(db, event, total_spots)
    _check_duplicate_guest(db, data.event_id, data.email)

    guest_price = Decimal(str(event.guest_price))

    # Apply promo code discount
    promo = None
    if data.promo_code:
        promo = _validate_promo_code(db, data.promo_code, data.event_id)
        guest_price = _apply_promo_discount(promo, guest_price, Decimal(str(event.member_price or 0)))

    sponsor = Decimal(str(data.sponsor_amount or 0)) if data.is_sponsor else Decimal("0")
    total   = guest_price + sponsor
    total += Decimal(str(event.guest_price)) * len(data.additional_golfers)  # additional golfers at original price

    # Charge card via North (skip for free events)
    charge = None
    if data.payment_token:
        try:
            charge = await charge_card(data.payment_token, float(total))
        except NorthDeclinedError as exc:
            logger.warning("Guest payment declined: email=%s event_id=%s", data.email, data.event_id)
            raise HTTPException(status_code=402, detail=str(exc))
        except NorthGatewayError as exc:
            logger.error("North error (guest): %s", exc)
            raise HTTPException(status_code=502, detail=str(exc))

    # Reuse existing Guest record or create one
    guest = db.query(Guest).filter(Guest.email == data.email).first()
    if not guest:
        guest = Guest(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
        )
        db.add(guest)
        db.flush()

    registration = EventRegistration(
        event_id=data.event_id,
        guest_id=guest.id,
        email=data.email,
        phone=data.phone,
        handicap=data.handicap,
        payment_status="paid" if charge else "free",
        payment_method="north" if charge else "none",
        amount_paid=float(guest_price + sponsor),
        transaction_id=charge.transaction_id if charge else None,
        is_sponsor=data.is_sponsor,
        sponsor_amount=float(data.sponsor_amount) if data.is_sponsor and data.sponsor_amount else None,
        company_name=data.company_name if data.is_sponsor else None,
    )
    db.add(registration)
    db.flush()

    guest_golfers = [
        AdditionalGolfer(
            is_member=False,
            first_name=g.first_name,
            last_name=g.last_name,
            email=g.email,
            phone=g.phone,
            handicap=g.handicap,
        )
        for g in data.additional_golfers
    ]
    additional_ids = _create_additional_registrations(
        db, event, guest_golfers,
        charge.transaction_id if charge else None, float(total),
    )

    # Increment promo code usage
    if promo:
        promo.times_used += 1

    db.commit()
    db.refresh(registration)

    logger.info(
        "Guest registered: registration_id=%s email=%s event_id=%s amount=%s additional=%d",
        registration.id, data.email, data.event_id, total, len(additional_ids),
    )

    # Send confirmation email
    try:
        registrant_name = f"{data.first_name} {data.last_name}"
        add_golfer_details = []
        for g in data.additional_golfers:
            name = f"{g.first_name or ''} {g.last_name or ''}".strip() or "Guest Golfer"
            add_golfer_details.append({"name": name, "price": float(guest_price)})

        EmailService().send_event_registration_email(
            to_email=data.email,
            registrant_name=registrant_name,
            event_name=event.golf_course,
            event_date=str(event.date),
            confirmation_id=_confirmation_id(registration.id),
            base_price=float(guest_price + sponsor),
            additional_golfers=add_golfer_details if add_golfer_details else None,
            sponsor_amount=float(data.sponsor_amount) if data.is_sponsor and data.sponsor_amount else None,
            total=float(total),
        )
    except Exception:
        logger.exception("Failed to send event registration email for registration_id=%s", registration.id)

    return RegistrationResponse(
        registration_id=registration.id,
        confirmation_id=_confirmation_id(registration.id),
        event_id=data.event_id,
        amount_charged=float(total),
        transaction_id=charge.transaction_id if charge else None,
        additional_ids=additional_ids,
    )


# ── Retry payment ───────────────────────────────────────────────────────────────

@router.post(
    "/{registration_id}/retry-payment",
    response_model=RegistrationResponse,
    status_code=status.HTTP_200_OK,
)
async def retry_payment(
    registration_id: int,
    data: RetryPaymentRequest,
    db: Session = Depends(get_db),
) -> RegistrationResponse:
    """
    Retry payment on a pending or failed registration using a new PayPal order.
    """
    registration = (
        db.query(EventRegistration)
        .filter(EventRegistration.id == registration_id)
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found.")

    if registration.payment_status == "paid":
        raise HTTPException(status_code=409, detail="This registration is already paid.")

    event = _get_event_or_404(db, registration.event_id)
    total = Decimal(str(registration.amount_paid or event.guest_price))

    try:
        charge = await charge_card(data.payment_token, float(total))
    except NorthDeclinedError as exc:
        raise HTTPException(status_code=402, detail=str(exc))
    except NorthGatewayError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    registration.payment_status  = "paid"
    registration.payment_method  = "north"
    registration.transaction_id  = charge.transaction_id
    db.commit()
    db.refresh(registration)

    return RegistrationResponse(
        registration_id=registration.id,
        confirmation_id=_confirmation_id(registration.id),
        event_id=registration.event_id,
        amount_charged=float(total),
        transaction_id=charge.transaction_id,
    )
