from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.dependencies import AdminUser
from models.scholarship_recipient import ScholarshipRecipient
from schemas.scholarship_recipient import (
    ScholarshipRecipientCreate,
    ScholarshipRecipientUpdate,
    ScholarshipRecipientResponse,
    ScholarshipRecipientPublic
)

router = APIRouter(prefix="/api", tags=["Scholarship Recipients"])


@router.get("/scholarship-recipients", response_model=List[ScholarshipRecipientPublic])
def get_public_recipients(db: Session = Depends(get_db)):
    """
    Get all scholarship recipients ordered by year (descending) and display_order.
    Public endpoint - no authentication required.
    """
    recipients = db.query(ScholarshipRecipient).order_by(
        ScholarshipRecipient.year.desc(),
        ScholarshipRecipient.display_order
    ).all()
    
    return recipients


@router.get("/scholarship-recipients/by-year/{year}", response_model=List[ScholarshipRecipientPublic])
def get_recipients_by_year(year: int, db: Session = Depends(get_db)):
    """
    Get scholarship recipients for a specific year.
    Public endpoint - no authentication required.
    """
    recipients = db.query(ScholarshipRecipient).filter(
        ScholarshipRecipient.year == year
    ).order_by(ScholarshipRecipient.display_order).all()
    
    return recipients


# ===================================================================
# ADMIN ENDPOINTS (Require admin authentication)
# ===================================================================

@router.get("/admin/scholarship-recipients", response_model=List[ScholarshipRecipientResponse])
def get_all_recipients(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Get all scholarship recipients (admin view).
    Requires admin authentication.
    """
    recipients = db.query(ScholarshipRecipient).order_by(
        ScholarshipRecipient.year.desc(),
        ScholarshipRecipient.display_order
    ).all()
    
    return recipients


@router.post("/admin/scholarship-recipients", response_model=ScholarshipRecipientResponse, status_code=status.HTTP_201_CREATED)
def create_recipient(
    recipient_data: ScholarshipRecipientCreate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Create a new scholarship recipient.
    Requires admin authentication.
    """
    recipient = ScholarshipRecipient(
        full_name=recipient_data.full_name,
        year=recipient_data.year,
        display_order=recipient_data.display_order
    )
    
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    
    return recipient


@router.put("/admin/scholarship-recipients/{recipient_id}", response_model=ScholarshipRecipientResponse)
def update_recipient(
    recipient_id: int,
    recipient_data: ScholarshipRecipientUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Update an existing scholarship recipient.
    Requires admin authentication.
    """
    recipient = db.query(ScholarshipRecipient).filter(
        ScholarshipRecipient.id == recipient_id
    ).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # Update only provided fields
    if recipient_data.full_name is not None:
        recipient.full_name = recipient_data.full_name
    if recipient_data.year is not None:
        recipient.year = recipient_data.year
    if recipient_data.display_order is not None:
        recipient.display_order = recipient_data.display_order
    
    db.commit()
    db.refresh(recipient)
    
    return recipient


@router.delete("/admin/scholarship-recipients/{recipient_id}")
def delete_recipient(
    recipient_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Delete a scholarship recipient.
    Requires admin authentication.
    """
    recipient = db.query(ScholarshipRecipient).filter(
        ScholarshipRecipient.id == recipient_id
    ).first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    db.delete(recipient)
    db.commit()
    
    return {"message": "Recipient deleted successfully", "id": recipient_id}
