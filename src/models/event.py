from sqlalchemy import Column, Integer, String, Date, Time, Numeric, Boolean
from core.database import Base


class Event(Base):
    __tablename__ = "event"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    township = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zipcode = Column(String, nullable=False)
    golf_course = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    member_price = Column(Numeric(10, 2), nullable=False)
    guest_price = Column(Numeric(10, 2), nullable=False)
    capacity = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
    registration_open = Column(Boolean, nullable=False, default=True, server_default="true")
    event_type = Column(String, nullable=False, default="regular", server_default="regular")