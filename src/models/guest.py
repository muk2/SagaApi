# models/guest.py

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from src.core.database import Base

class Guest(Base):
    __tablename__ = "guest"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    handicap_index = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)