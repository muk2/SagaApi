from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.event import EventRead
from services.event_service import list_events

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("/", response_model=list[EventRead])
def get_events(db: Session = Depends(get_db)):
    return list_events(db)
