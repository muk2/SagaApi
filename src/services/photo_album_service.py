from sqlalchemy.orm import Session
from repositories.photo_album_repository import PhotoAlbumRepository
from schemas.photo_album import PhotoAlbumCreate, PhotoAlbumUpdate, PhotoAlbumResponse
from typing import List

class PhotoAlbumService:
    def __init__(self, db: Session):
        self.repo = PhotoAlbumRepository(db)
    
    def get_all_albums(self) -> List[PhotoAlbumResponse]:
        albums = self.repo.get_all()
        return [PhotoAlbumResponse.from_orm(album) for album in albums]
    
    def create_album(self, album_data: PhotoAlbumCreate) -> PhotoAlbumResponse:
        album = self.repo.create(album_data.dict())
        return PhotoAlbumResponse.from_orm(album)
    
    def update_album(self, album_id: int, album_data: PhotoAlbumUpdate) -> PhotoAlbumResponse:
        album = self.repo.update(album_id, album_data.dict())
        if not album:
            raise ValueError("Album not found")
        return PhotoAlbumResponse.from_orm(album)
    
    def delete_album(self, album_id: int) -> bool:
        return self.repo.delete(album_id)