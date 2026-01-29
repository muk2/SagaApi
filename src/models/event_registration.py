from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class EventRegistration(Base):
    """
    Represents a user's registration for an event.
    Links users to events with registration timestamp.
    """

    __tablename__ = "event_registration"
    __table_args__ = {"schema": "saga"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saga.user.id"), nullable=False, index=True
    )
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("saga.event.id"), nullable=False, index=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="confirmed")

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    event: Mapped["Event"] = relationship("Event", foreign_keys=[event_id])
