from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.member_membership import MemberMembership


class MembershipTier(Base):
    """
    Represents a membership tier with pricing.
    Defines the available membership levels (e.g., Individual, Student).
    """

    __tablename__ = "membership_tiers"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Relationships
    memberships: Mapped[list[MemberMembership]] = relationship(
        "MemberMembership", back_populates="tier"
    )
