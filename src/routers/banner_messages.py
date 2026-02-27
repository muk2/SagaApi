from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from src.core.database import get_db
from src.schemas.banner_message import BannerRead
from src.services.banner_service import list_banners, update_display_count, update_messages


router = APIRouter(prefix="/api/banner_messages", tags=["Banner Messages"])

class MessageItem(BaseModel):
    id: int = None
    message: str

class UpdateMessagesRequest(BaseModel):
    messages: List[MessageItem]

@router.get("/")  
def get_banner_messages(db: Session = Depends(get_db)):
    """Get banner messages with display count."""
    return list_banners(db)

@router.put("/display-count")
def update_banner_display_count(
    count: int,
    db: Session = Depends(get_db)
):
    """Update banner display count (admin only - add auth if needed)."""
    new_count = update_display_count(db, count)
    return {
        "message": "Display count updated successfully",
        "display_count": new_count
    }


@router.put("/messages")
def update_banner_messages_endpoint(
    request: UpdateMessagesRequest,
    db: Session = Depends(get_db)
):
    """Update banner messages."""
    messages = [{"message": msg.message} for msg in request.messages]
    updated = update_messages(db, messages)
    return {
        "message": "Banner messages updated successfully",
        "messages": updated
    }