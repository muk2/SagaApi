from sqlalchemy.orm import Session

from models.banner_message import Banner


def get_banners(db: Session):
    return db.query(Banner).all()