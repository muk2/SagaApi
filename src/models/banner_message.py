from sqlalchemy import Column, Integer, String
from core.database import Base


class Banner(Base):
    __tablename__ = "banner_messages"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    