from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.membership_tier import MembershipTier
    from models.payment import Payment
    from models.user import User


class MemberMembership(Base):
    """
    Represents a user's membership for a given season year.
    Links a user to a membership tier with payment tracking.
    """

    __tablename__ = "member_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "season_year"),
        {"schema": "saga"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saga.user.id"), nullable=False, index=True
    )
    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saga.membership_tiers.id"), nullable=False
    )
    payment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    marked_paid_by_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )

    # Relationships
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    tier: Mapped[MembershipTier] = relationship("MembershipTier", back_populates="memberships")
    payments: Mapped[List[Payment]] = relationship("Payment", back_populates="membership")
