from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from services.admin_service import AdminService
from schemas.admin import PhotoAlbumResponse

router = APIRouter(prefix="/api/photo-albums", tags=["Photo Albums"])

@router.get("/", response_model=List[PhotoAlbumResponse])
def get_all_albums(db: Session = Depends(get_db)):
    """Get all photo albums (public endpoint)."""
    service = AdminService(db)
    albums = service.get_all_photo_albums()
    return albums