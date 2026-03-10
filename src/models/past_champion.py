from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from core.database import Base


class PastChampion(Base):
    __tablename__ = "past_champions"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())