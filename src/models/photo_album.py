from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PhotoAlbum(Base):
    """
    Represents a photo album.
    Contains album metadata and images.
    """

    __tablename__ = "photo_album"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    images: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array of image URLs
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(), onupdate=lambda: datetime.now()
    )
