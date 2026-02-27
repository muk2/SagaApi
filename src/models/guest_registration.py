from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class GuestRegistration(Base):
    """
    Represents a guest (non-member) registration.
    Captures contact info for guests who register for events.
    """

    __tablename__ = "guest_registrations"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    handicap: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referral_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
