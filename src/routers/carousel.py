from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from repositories.carousel_repository import CarouselRepository

router = APIRouter(prefix="/api/carousel", tags=["Carousel"])

@router.get("/")
def get_carousel_images(db: Session = Depends(get_db)):
    """Get carousel images (public endpoint)."""
    repo = CarouselRepository(db)
    images = repo.get_all_images()
    return {"images": images}