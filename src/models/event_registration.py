from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.event import Event
    from models.user import User


class EventRegistration(Base):
    """
    Represents a user's registration for an event.
    Links users to events with registration timestamp.
    """

    __tablename__ = "event_registration"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saga.event.id"), nullable=False, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("saga.user.id"), nullable=True, index=True
    )
    guest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_tier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    handicap: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True)
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Relationships
    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id])
    event: Mapped[Event] = relationship("Event", foreign_keys=[event_id])
