from sqlalchemy import Column, Integer, Text, Numeric, DateTime
from sqlalchemy.sql import func
from core.database import Base


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entry"
    __table_args__ = {"schema": "saga"}

    id               = Column(Integer, primary_key=True, index=True)
    position         = Column(Integer, nullable=False)
    first_name       = Column(Text, nullable=False)
    last_name        = Column(Text, nullable=False)
    stableford_points = Column(Numeric(7, 1), nullable=False)
    total_gross      = Column(Numeric(7, 1), nullable=True)
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
