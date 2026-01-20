from sqlalchemy.orm import Session
from repositories.event_repository import get_events


def list_events(db: Session):
    return get_events(db)