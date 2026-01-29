from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from schemas.banner_message import BannerRead
from services.banner_service import list_banners



router = APIRouter(prefix="/api/banner_messages", tags=["Banner Messages"])


@router.get("/", response_model=List[BannerRead])

def get_banner_messages(db: Session = Depends(get_db)):
    return list_banners(db)