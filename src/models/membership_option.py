from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime
from sqlalchemy.sql import func
from core.database import Base

class MembershipOption(Base):
    __tablename__ = "membership_options"
    __table_args__ = {"schema": "saga"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    display_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())