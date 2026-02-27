from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from typing import Optional

class SiteContent(Base):
    """
    Represents site-wide content settings.
    Stores configurable text content for the website.
    """

    __tablename__ = "site_content"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )
