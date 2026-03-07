"""
Registrations Router
Handles event registration for both authenticated members and guests.
Payment via North is required — registration is only saved after a successful charge.

Endpoints:
  POST /api/registrations              — authenticated member registers
  POST /api/registrations/guest        — unauthenticated guest registers
  POST /api/registrations/{id}/retry-payment  — retry a failed/pending payment
"""
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
from services.north_payment_service import (
    NorthDeclinedError,
    NorthGatewayError,
    charge_card,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/registrations", tags=["Registrations"])


# ── Schemas ─────────────────────────────────────────────────────────────────────

class MemberRegistrationRequest(BaseModel):
    event_id:        int
    payment_token:   str
    idempotency_key: str = Field(min_length=10)
    handicap:        Optional[str]   = None
    is_sponsor:      bool            = False
    sponsor_amount:  Optional[float] = None
    company_name:    Optional[str]   = None


class GuestRegistrationRequest(BaseModel):
    event_id:        int
    payment_token:   str
    idempotency_key: str = Field(min_length=10)
    first_name:      str
    last_name:       str
    email:           EmailStr
    phone:           str
    handicap:        Optional[str]   = None
    is_sponsor:      bool            = False
    sponsor_amount:  Optional[float] = None
    company_name:    Optional[str]   = None


class RetryPaymentRequest(BaseModel):
    payment_token:   str
    idempotency_key: str = Field(min_length=10)


class RegistrationResponse(BaseModel):
    registration_id: int
    confirmation_id: str
    event_id:        int
    amount_charged:  float
    transaction_id:  Optional[str] = None
    card_last_four:  Optional[str] = None
    message:         str = "Registration confirmed"


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_event_or_404(db: Session, event_id: int) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


def _check_capacity(db: Session, event: Event) -> None:
    registered = (
        db.query(EventRegistration)
        .filter(EventRegistration.event_id == event.id)
        .count()
    )
    if registered >= event.capacity:
        raise HTTPException(status_code=409, detail="This event is fully booked.")


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


# ── Member registration ─────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_member(
    data: MemberRegistrationRequest,
    current_user=Depends(CurrentUser),
    db: Session = Depends(get_db),
) -> RegistrationResponse:
    """
    Register an authenticated member.
    Charges member_price (+ optional sponsorship amount).
    Registration row is only inserted after a successful payment.
    """
    event = _get_event_or_404(db, data.event_id)
    _check_capacity(db, event)
    _check_duplicate_member(db, data.event_id, current_user.id)

    base    = Decimal(str(event.member_price or event.guest_price))
    sponsor = Decimal(str(data.sponsor_amount or 0)) if data.is_sponsor else Decimal("0")
    total   = base + sponsor

    try:
        charge = await charge_card(data.payment_token, float(total))
    except NorthDeclinedError as exc:
        logger.warning(
            "Member payment declined: user_id=%s event_id=%s",
            current_user.id, data.event_id,
        )
        raise HTTPException(status_code=402, detail=str(exc))
    except NorthGatewayError as exc:
        logger.error("North gateway error (member): %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    registration = EventRegistration(
        event_id=data.event_id,
        user_id=current_user.id,
        email=getattr(current_user, "email", None),
        phone=getattr(current_user, "phone_number", None),
        handicap=data.handicap,
        payment_status="paid",
        payment_method="card",
        amount_paid=float(total),
        transaction_id=charge.transaction_id,
        north_uniq_id=charge.uniq_id,
        north_account_id=charge.account_id,
        card_last_four=charge.card_last_four,
        idempotency_key=data.idempotency_key,
        is_sponsor=data.is_sponsor,
        sponsor_amount=float(data.sponsor_amount) if data.is_sponsor and data.sponsor_amount else None,
        company_name=data.company_name if data.is_sponsor else None,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    logger.info(
        "Member registered: registration_id=%s user_id=%s event_id=%s amount=%s",
        registration.id, current_user.id, data.event_id, total,
    )

    return RegistrationResponse(
        registration_id=registration.id,
        confirmation_id=_confirmation_id(registration.id),
        event_id=data.event_id,
        amount_charged=float(total),
        transaction_id=charge.transaction_id,
        card_last_four=charge.card_last_four,
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
    Register an unauthenticated guest.
    Charges guest_price (+ optional sponsorship amount).
    Registration row is only inserted after a successful payment.
    """
    event = _get_event_or_404(db, data.event_id)
    _check_capacity(db, event)
    _check_duplicate_guest(db, data.event_id, data.email)

    base    = Decimal(str(event.guest_price))
    sponsor = Decimal(str(data.sponsor_amount or 0)) if data.is_sponsor else Decimal("0")
    total   = base + sponsor

    try:
        charge = await charge_card(data.payment_token, float(total))
    except NorthDeclinedError as exc:
        logger.warning(
            "Guest payment declined: email=%s event_id=%s", data.email, data.event_id
        )
        raise HTTPException(status_code=402, detail=str(exc))
    except NorthGatewayError as exc:
        logger.error("North gateway error (guest): %s", exc)
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
        payment_status="paid",
        payment_method="card",
        amount_paid=float(total),
        transaction_id=charge.transaction_id,
        north_uniq_id=charge.uniq_id,
        north_account_id=charge.account_id,
        card_last_four=charge.card_last_four,
        idempotency_key=data.idempotency_key,
        is_sponsor=data.is_sponsor,
        sponsor_amount=float(data.sponsor_amount) if data.is_sponsor and data.sponsor_amount else None,
        company_name=data.company_name if data.is_sponsor else None,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    logger.info(
        "Guest registered: registration_id=%s email=%s event_id=%s amount=%s",
        registration.id, data.email, data.event_id, total,
    )

    return RegistrationResponse(
        registration_id=registration.id,
        confirmation_id=_confirmation_id(registration.id),
        event_id=data.event_id,
        amount_charged=float(total),
        transaction_id=charge.transaction_id,
        card_last_four=charge.card_last_four,
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
    Retry payment on a pending or failed registration.
    The frontend stores the registration_id when a first attempt is created
    but payment fails, then calls this endpoint with a new card token.
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
    registration.payment_method  = "card"
    registration.transaction_id  = charge.transaction_id
    registration.north_uniq_id   = charge.uniq_id
    registration.north_account_id = charge.account_id
    registration.card_last_four  = charge.card_last_four
    registration.idempotency_key = data.idempotency_key
    db.commit()
    db.refresh(registration)

    return RegistrationResponse(
        registration_id=registration.id,
        confirmation_id=_confirmation_id(registration.id),
        event_id=registration.event_id,
        amount_charged=float(total),
        transaction_id=charge.transaction_id,
        card_last_four=charge.card_last_four,
    )