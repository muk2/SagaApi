from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PaymentMethod(Base):
    """
    Represents a payment method type (e.g., credit_card, cash, check).
    Lookup table for normalizing payment method references.
    """

    __tablename__ = "payment_methods"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
