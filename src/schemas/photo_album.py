from pydantic import BaseModel
from datetime import date

class PhotoAlbumBase(BaseModel):
    title: str
    date: date
    cover_image: str
    google_drive_link: str

class PhotoAlbumCreate(PhotoAlbumBase):
    pass

class PhotoAlbumUpdate(PhotoAlbumBase):
    pass

class PhotoAlbumResponse(PhotoAlbumBase):
    id: int
    
    class Config:
        from_attributes = True