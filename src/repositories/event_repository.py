from sqlalchemy.orm import Session
from models.event import Event


def get_events(db: Session):
    return db.query(Event).all()