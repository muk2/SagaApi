from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core.dependencies import AdminUser
from models.past_champion import PastChampion
from schemas.past_champion import (
    PastChampionCreate,
    PastChampionUpdate,
    PastChampionResponse,
    PastChampionPublic,
)


router = APIRouter(prefix="/api", tags=["Past Champions"])

# ===================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ===================================================================

@router.get("/past-champions", response_model=List[PastChampionPublic])
def get_past_champions(db: Session = Depends(get_db)):
    """
    Get all past champions ordered by year descending (most recent first).
    Public endpoint — no authentication required.
    """
    champions = (
        db.query(PastChampion)
        .order_by(PastChampion.year.desc())
        .all()
    )
    return champions


# ===================================================================
# ADMIN ENDPOINTS (Require admin authentication)
# ===================================================================

@router.get("/admin/past-champions", response_model=List[PastChampionResponse])
def get_all_past_champions_admin(
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Get all past champions with full details.
    Requires admin authentication.
    """
    champions = (
        db.query(PastChampion)
        .order_by(PastChampion.year.desc())
        .all()
    )
    return champions


@router.post(
    "/admin/past-champions",
    response_model=PastChampionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_past_champion(
    champion_data: PastChampionCreate,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Create a new past champion entry.
    Requires admin authentication.
    """
    # Check for duplicate year
    existing = (
        db.query(PastChampion)
        .filter(PastChampion.year == champion_data.year)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A champion for year {champion_data.year} already exists. Edit the existing entry instead.",
        )

    champion = PastChampion(
        name=champion_data.name,
        year=champion_data.year,
    )

    db.add(champion)
    db.commit()
    db.refresh(champion)

    return champion


@router.put("/admin/past-champions/{champion_id}", response_model=PastChampionResponse)
def update_past_champion(
    champion_id: int,
    champion_data: PastChampionUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Update an existing past champion entry.
    Requires admin authentication.
    """
    champion = (
        db.query(PastChampion)
        .filter(PastChampion.id == champion_id)
        .first()
    )

    if not champion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Past champion not found",
        )

    # If updating the year, check for duplicates
    if champion_data.year is not None and champion_data.year != champion.year:
        existing = (
            db.query(PastChampion)
            .filter(PastChampion.year == champion_data.year)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A champion for year {champion_data.year} already exists.",
            )
        champion.year = champion_data.year

    if champion_data.name is not None:
        champion.name = champion_data.name

    db.commit()
    db.refresh(champion)

    return champion


@router.delete("/admin/past-champions/{champion_id}")
def delete_past_champion(
    champion_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Delete a past champion entry.
    Requires admin authentication.
    """
    champion = (
        db.query(PastChampion)
        .filter(PastChampion.id == champion_id)
        .first()
    )

    if not champion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Past champion not found",
        )

    db.delete(champion)
    db.commit()

    return {"message": "Past champion deleted successfully", "id": champion_id}