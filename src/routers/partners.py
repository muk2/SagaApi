from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.repositories.partner_repository import PartnerRepository

router = APIRouter(prefix="/api/partners", tags=["Partners"])

@router.get("/")
def get_all_partners(db: Session = Depends(get_db)):
    """Get all partners (public endpoint)."""
    repo = PartnerRepository(db)
    partners = repo.get_all()
    
    return [
        {
            'id': p.id,
            'name': p.name,
            'logo_url': p.logo_url,
            'website_url': p.website_url,
            'display_order': p.display_order
        }
        for p in partners
    ]