from sqlalchemy.orm import Session


from repositories.banner_repository import (
    get_banners, 
    get_banner_display_count,  
    update_banner_display_count,
    update_banner_messages  
)

def list_banners(db: Session):
    """Get banners with display count."""
    banners = get_banners(db)
    display_count = get_banner_display_count(db)
    
    return {
        "messages": [{"id": b.id, "message": b.message} for b in banners],
        "display_count": display_count
    }


def update_display_count(db: Session, count: int):
    """Update banner display count."""
    return update_banner_display_count(db, count)

def update_messages(db: Session, messages: list):
    """Update banner messages."""
    updated_banners = update_banner_messages(db, messages)
    return [{"id": b.id, "message": b.message} for b in updated_banners]