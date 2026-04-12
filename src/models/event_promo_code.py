from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class EventPromoCode(Base):
    """
    Promo codes for event registrations.
    Admins can create codes that give discounts:
      - 'member_price': guest pays member price
      - 'free': event is free
      - 'percent': percentage discount off the base price
    """

    __tablename__ = "event_promo_code"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False
        # Values: "member_price" | "free" | "percent"
    )
    discount_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True,
        comment="Percentage value for 'percent' type (e.g. 20 for 20% off)"
    )
    event_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.event.id"), nullable=True,
        comment="NULL means code applies to all events"
    )
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    times_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    event = relationship("Event", foreign_keys=[event_id], lazy="joined")
