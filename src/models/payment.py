from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.event_registration import EventRegistration
    from models.member_membership import MemberMembership
    from models.payment_method import PaymentMethod


class Payment(Base):
    """
    Represents a payment transaction.
    Tracks event registration payments and membership payments,
    including North payment gateway integration data.
    """

    __tablename__ = "payments"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    registration_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("saga.event_registration.id"), nullable=True
    )
    membership_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("saga.member_memberships.id"), nullable=True
    )
    payment_method_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("saga.payment_methods.id"), nullable=True
    )
    payment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="event_registration"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    north_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    north_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Relationships
    registration: Mapped[EventRegistration | None] = relationship(
        "EventRegistration", foreign_keys=[registration_id]
    )
    membership: Mapped[MemberMembership | None] = relationship(
        "MemberMembership", back_populates="payments", foreign_keys=[membership_id]
    )
    method: Mapped[PaymentMethod | None] = relationship(
        "PaymentMethod", foreign_keys=[payment_method_id]
    )
