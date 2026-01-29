from __future__ import annotations
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from core.database import Base


class User(Base):
    """
    Represents a golfer's profile (non-auth).
    Contains name, handicap, and phone number.
    """

    __tablename__ = "user"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    handicap: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_account_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("saga.user_account.id"), nullable=True
    )

    account: Mapped["UserAccount | None"] = relationship(
        "UserAccount", back_populates="user", foreign_keys="UserAccount.user_id"
    )


class UserAccount(Base):
    """
    Represents login credentials and identity.
    Supports authentication with email/password.
    """

    __tablename__ = "user_account"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("saga.user.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_logged_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="account", foreign_keys=[user_id])
