from sqlalchemy.orm import Session

from repositories.banner_repository import get_banners


def list_banners(db: Session):
    return get_banners(db)