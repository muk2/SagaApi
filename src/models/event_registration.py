from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.event import Event
    from src.models.guest import Guest
    from src.models.user import UserAccount


class EventRegistration(Base):
    __tablename__ = "event_registration"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saga.event.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.user_account.id"), nullable=True, index=True
    )
    guest_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.guest.id"), nullable=True
    )
    price_tier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    handicap: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payment_status: Mapped[str] = mapped_column(String, nullable=False, default="paid")
    payment_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    amount_paid: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    user_account: Mapped[Optional["UserAccount"]] = relationship(
        "UserAccount", foreign_keys=[user_id], lazy="joined"
    )
    guest: Mapped[Optional["Guest"]] = relationship("Guest", foreign_keys=[guest_id])
    event: Mapped["Event"] = relationship("Event", foreign_keys=[event_id])
