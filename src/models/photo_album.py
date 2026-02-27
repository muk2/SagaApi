from sqlalchemy import Column, Integer, String, Date
from src.core.database import Base

class PhotoAlbum(Base):
    __tablename__ = "photo_albums"
    __table_args__ = {"schema": "saga"}
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    cover_image = Column(String, nullable=False)
    google_drive_link = Column(String, nullable=False)
