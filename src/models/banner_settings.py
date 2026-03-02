from sqlalchemy import Column, Integer
from core.database import Base


class BannerSettings(Base):
    __tablename__ = "banner_settings"
    __table_args__ = {"schema": "saga"}

    count = Column(Integer, primary_key=True, nullable=False)
