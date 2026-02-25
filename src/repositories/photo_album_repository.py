from sqlalchemy.orm import Session
from models.photo_album import PhotoAlbum
from typing import List, Optional

class PhotoAlbumRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[PhotoAlbum]:
        return self.db.query(PhotoAlbum).order_by(PhotoAlbum.date.desc()).all()
    
    def get_by_id(self, album_id: int) -> Optional[PhotoAlbum]:
        return self.db.query(PhotoAlbum).filter(PhotoAlbum.id == album_id).first()
    
    def create(self, album_data: dict) -> PhotoAlbum:
        album = PhotoAlbum(**album_data)
        self.db.add(album)
        self.db.commit()
        self.db.refresh(album)
        return album
    
    def update(self, album_id: int, album_data: dict) -> Optional[PhotoAlbum]:
        album = self.get_by_id(album_id)
        if not album:
            return None
        
        for key, value in album_data.items():
            setattr(album, key, value)
        
        self.db.commit()
        self.db.refresh(album)
        return album
    
    def delete(self, album_id: int) -> bool:
        album = self.get_by_id(album_id)
        if not album:
            return False
        
        self.db.delete(album)
        self.db.commit()
        return True