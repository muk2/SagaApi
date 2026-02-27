from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from src.core.database import Base

class ScholarshipRecipient(Base):
    __tablename__ = "scholarship_recipients"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    bio = Column(Text)
    display_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
