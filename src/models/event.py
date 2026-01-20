from sqlalchemy import Column, Integer, String
from core.database import Base


class Event(Base):
    __tablename__ = "event"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    township = Column(String, nullable=False)
    golf_course = Column(String, nullable=False)