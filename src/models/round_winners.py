from sqlalchemy import Column, Integer, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from core.database import Base


class RoundWinners(Base):
    __tablename__ = "round_winners"
    __table_args__ = {"schema": "saga"}

    id                       = Column(Integer, primary_key=True, index=True)
    event_id                 = Column(Integer, ForeignKey("saga.event.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, unique=True)
    lowest_gross_winner      = Column(Text, nullable=True)
    lowest_gross_score       = Column(Numeric(5, 1), nullable=True)
    stableford_winner        = Column(Text, nullable=True)
    stableford_points        = Column(Numeric(5, 1), nullable=True)
    straightest_drive_winner   = Column(Text, nullable=True)
    straightest_drive_hole     = Column(Text, nullable=True)
    straightest_drive_distance = Column(Text, nullable=True)
    close_to_pin             = Column(JSONB, default=list)
    sponsors                 = Column(JSONB, default=list)   # [{sponsor_name, company_name}, ...]
    created_at               = Column(DateTime(timezone=True), server_default=func.now())
    updated_at               = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


