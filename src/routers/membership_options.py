from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.core.dependencies import AdminUser
from src.models.membership_option import MembershipOption
from src.schemas.membership_option import MembershipOptionCreate,MembershipOptionUpdate,MembershipOptionResponse,MembershipOptionPublic


router = APIRouter(prefix="/api", tags=["Membership Options"])

# ===================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ===================================================================

@router.get("/membership-options", response_model=List[MembershipOptionPublic])
def get_active_membership_options(db: Session = Depends(get_db)):
    """
    Get all active membership options ordered by display_order.
    Public endpoint - no authentication required.
    """
    options = db.query(MembershipOption).filter(
        MembershipOption.is_active == True
    ).order_by(MembershipOption.display_order).all()
    
    return options


# ===================================================================
# ADMIN ENDPOINTS (Require admin authentication)
# ===================================================================

@router.get("/admin/membership-options", response_model=List[MembershipOptionResponse])
def get_all_membership_options(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Get all membership options (including inactive ones).
    Requires admin authentication.
    """
    options = db.query(MembershipOption).order_by(
        MembershipOption.display_order
    ).all()
    
    return options


@router.post("/admin/membership-options", response_model=MembershipOptionResponse, status_code=status.HTTP_201_CREATED)
def create_membership_option(
    option_data: MembershipOptionCreate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Create a new membership option.
    Requires admin authentication.
    """
    option = MembershipOption(
        name=option_data.name,
        price=option_data.price,
        description=option_data.description,
        is_active=option_data.is_active,
        display_order=option_data.display_order
    )
    
    db.add(option)
    db.commit()
    db.refresh(option)
    
    return option


@router.put("/admin/membership-options/{option_id}", response_model=MembershipOptionResponse)
def update_membership_option(
    option_id: int,
    option_data: MembershipOptionUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Update an existing membership option.
    Requires admin authentication.
    """
    option = db.query(MembershipOption).filter(
        MembershipOption.id == option_id
    ).first()
    
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership option not found"
        )
    
    # Update only provided fields
    if option_data.name is not None:
        option.name = option_data.name
    if option_data.price is not None:
        option.price = option_data.price
    if option_data.description is not None:
        option.description = option_data.description
    if option_data.is_active is not None:
        option.is_active = option_data.is_active
    if option_data.display_order is not None:
        option.display_order = option_data.display_order
    
    db.commit()
    db.refresh(option)
    
    return option


@router.delete("/admin/membership-options/{option_id}")
def delete_membership_option(
    option_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Delete a membership option.
    Requires admin authentication.
    """
    option = db.query(MembershipOption).filter(
        MembershipOption.id == option_id
    ).first()
    
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership option not found"
        )
    
    db.delete(option)
    db.commit()
    
    return {"message": "Membership option deleted successfully", "id": option_id}