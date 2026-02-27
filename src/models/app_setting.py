from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.user import User


class AppSetting(Base):
    """
    Represents an application-level configuration setting.
    Stores key-value pairs for runtime configuration (e.g., guest_event_rate).
    """

    __tablename__ = "app_settings"
    __table_args__ = {"schema": "saga"}

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("saga.user.id"), nullable=True
    )

    # Relationships
    updated_by_user: Mapped[User | None] = relationship("User", foreign_keys=[updated_by])
