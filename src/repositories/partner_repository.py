from sqlalchemy.orm import Session
from models.partner import Partner
from typing import List, Optional


class PartnerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Partner]:
        """Get all partners ordered by display_order."""
        return self.db.query(Partner).order_by(Partner.display_order).all()

    def get_by_id(self, partner_id: int) -> Optional[Partner]:
        """Get partner by ID."""
        return self.db.query(Partner).filter(Partner.id == partner_id).first()

    def create(self, name: str, logo_url: str, website_url: Optional[str], display_order: int) -> Partner:
        """Create new partner."""
        partner = Partner(
            name=name,
            logo_url=logo_url,
            website_url=website_url,
            display_order=display_order
        )
        self.db.add(partner)
        self.db.commit()
        self.db.refresh(partner)
        return partner

    def update(self, partner_id: int, **kwargs) -> Optional[Partner]:
        """Update partner."""
        partner = self.get_by_id(partner_id)
        if not partner:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(partner, key):
                setattr(partner, key, value)

        self.db.commit()
        self.db.refresh(partner)
        return partner

    def delete(self, partner_id: int) -> bool:
        """Delete partner."""
        partner = self.get_by_id(partner_id)
        if not partner:
            return False

        self.db.delete(partner)
        self.db.commit()
        return True