# ===================================================================
# File: routers/faq.py
# FAQ Router - Public and Admin endpoints
# ===================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.core.dependencies import AdminUser
from src.models.faq import FAQ
from src.schemas.faq import FAQCreate, FAQUpdate, FAQResponse, FAQPublic

router = APIRouter(prefix="/api", tags=["FAQ"])

# ===================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ===================================================================

@router.get("/faqs", response_model=List[FAQPublic])
def get_public_faqs(db: Session = Depends(get_db)):
    """
    Get all active FAQs ordered by display_order.
    Public endpoint - no authentication required.
    """
    faqs = db.query(FAQ).filter(
        FAQ.is_active == True
    ).order_by(FAQ.display_order).all()
    
    return faqs


# ===================================================================
# ADMIN ENDPOINTS (Require admin authentication)
# ===================================================================

@router.get("/admin/faqs", response_model=List[FAQResponse])
def get_all_faqs(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Get all FAQs (including inactive ones).
    Requires admin authentication.
    """
    faqs = db.query(FAQ).order_by(FAQ.display_order).all()
    return faqs


@router.post("/admin/faqs", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
def create_faq(
    faq_data: FAQCreate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Create a new FAQ.
    Requires admin authentication.
    """
    faq = FAQ(
        question=faq_data.question,
        answer=faq_data.answer,
        display_order=faq_data.display_order,
        is_active=faq_data.is_active
    )
    
    db.add(faq)
    db.commit()
    db.refresh(faq)
    
    return faq


@router.put("/admin/faqs/{faq_id}", response_model=FAQResponse)
def update_faq(
    faq_id: int,
    faq_data: FAQUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Update an existing FAQ.
    Requires admin authentication.
    """
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    # Update only provided fields
    if faq_data.question is not None:
        faq.question = faq_data.question
    if faq_data.answer is not None:
        faq.answer = faq_data.answer
    if faq_data.display_order is not None:
        faq.display_order = faq_data.display_order
    if faq_data.is_active is not None:
        faq.is_active = faq_data.is_active
    
    db.commit()
    db.refresh(faq)
    
    return faq


@router.delete("/admin/faqs/{faq_id}")
def delete_faq(
    faq_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Delete an FAQ.
    Requires admin authentication.
    """
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FAQ not found"
        )
    
    db.delete(faq)
    db.commit()
    
    return {"message": "FAQ deleted successfully", "id": faq_id}