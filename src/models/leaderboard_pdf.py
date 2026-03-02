from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func
from core.database import Base


class LeaderboardPdf(Base):
    __tablename__ = "leaderboard_pdf"
    __table_args__ = {"schema": "saga"}

    id         = Column(Integer, primary_key=True, index=True)
    url        = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

