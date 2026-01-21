from datetime import date, time
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Event(Base):
    """
    Represents a golf event/tournament.
    This is the anchor table for the event management system.
    """

    __tablename__ = "event"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    township: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    zipcode: Mapped[int] = mapped_column(Integer, nullable=False)
    golf_course: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Relationships
    price_tiers: Mapped[list["EventPriceTier"]] = relationship(
        "EventPriceTier", back_populates="event", cascade="all, delete-orphan"
    )


class EventPriceTier(Base):
    """
    Represents pricing options for an event (e.g. "Early Bird", "Member", "Guest").
    Tiers can be activated/deactivated without deletion for historical integrity.
    """

    __tablename__ = "event_price_tier"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("saga.event.id"), nullable=False)
    tier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="price_tiers")
