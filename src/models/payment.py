from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.event_registration import EventRegistration
    from models.member_membership import MemberMembership
    from models.payment_method import PaymentMethod


class Payment(Base):
    __tablename__ = "payment"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    registration_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.event_registration.id"), nullable=True
    )
    membership_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.member_memberships.id"), nullable=True
    )
    method_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.payment_method.id"), nullable=True
    )
    payment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="event_registration"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    external_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    zelle_note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    north_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    north_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    marked_paid_by_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    registration: Mapped[Optional["EventRegistration"]] = relationship(
        "EventRegistration", foreign_keys=[registration_id]
    )
    membership: Mapped[Optional["MemberMembership"]] = relationship(
        "MemberMembership", back_populates="payments", foreign_keys=[membership_id]
    )
    method: Mapped[Optional["PaymentMethod"]] = relationship(
        "PaymentMethod", foreign_keys=[method_id]
    )
