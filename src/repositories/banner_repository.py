from sqlalchemy.orm import Session

from src.models.banner_message import Banner
from src.models.banner_settings import BannerSettings

def get_banners(db: Session):
    return db.query(Banner).all()

def get_banner_display_count(db: Session) -> int:
    """Get the display count from banner_settings table."""
    settings = db.query(BannerSettings).first()
    return settings.count if settings else 3

def update_banner_display_count(db: Session, count: int) -> int:
    """Update the display count in banner_settings table."""
    settings = db.query(BannerSettings).first()
    
    if not settings:
        # Create new settings record
        settings = BannerSettings(count=count)
        db.add(settings)
    else:
        # Update existing
        settings.count = count
    
    db.commit()
    db.refresh(settings)
    return settings.count


def update_banner_messages(db: Session, messages: list):
    """Update all banner messages."""
    # Delete all existing banners
    db.query(Banner).delete()
    
    # Add new banners
    for msg in messages:
        banner = Banner(message=msg['message'])
        db.add(banner)
    
    db.commit()
    
    # Return updated banners
    return db.query(Banner).all()