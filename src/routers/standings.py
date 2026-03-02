import json
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AdminUser
from models.leaderboard_pdf import LeaderboardPdf
from models.round_winners import RoundWinners
from schemas.standings import (
    RoundWinnersCreate,
    RoundWinnersUpdate,
    RoundWinnersResponse,
    LeaderboardPdfResponse,
)

router = APIRouter(prefix="/api", tags=["Standings"])

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads/leaderboard")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ===================================================================
# LEADERBOARD PDF ENDPOINTS
# ===================================================================

@router.get("/leaderboard/pdf", response_model=LeaderboardPdfResponse)
def get_leaderboard_pdf(db: Session = Depends(get_db)):
    """
    Get the current leaderboard PDF URL.
    Public endpoint - no authentication required.
    """
    record = db.query(LeaderboardPdf).order_by(LeaderboardPdf.id.desc()).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leaderboard PDF uploaded yet"
        )

    return record


@router.post("/leaderboard/pdf", response_model=LeaderboardPdfResponse, status_code=status.HTTP_201_CREATED)
def upload_leaderboard_pdf(
    file: UploadFile = File(...),
    admin_user: AdminUser = None,
    db: Session = Depends(get_db)
):
    """
    Upload or replace the leaderboard PDF.
    Requires admin authentication.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted"
        )

    filename = f"leaderboard_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    url = f"/uploads/leaderboard/{filename}"

    # Single-row table — delete existing before inserting new
    db.query(LeaderboardPdf).delete()
    record = LeaderboardPdf(url=url)
    db.add(record)
    db.commit()
    db.refresh(record)

    return record


# ===================================================================
# PUBLIC ROUND WINNERS ENDPOINTS
# ===================================================================

@router.get("/round-winners/{event_id}", response_model=RoundWinnersResponse)
def get_round_winners(event_id: int, db: Session = Depends(get_db)):
    """
    Get round winners for a specific event.
    Public endpoint - no authentication required.
    """
    record = db.query(RoundWinners).filter(
        RoundWinners.event_id == event_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results recorded for this event"
        )

    return record


# ===================================================================
# ADMIN ROUND WINNERS ENDPOINTS (Require admin authentication)
# ===================================================================

@router.post("/admin/round-winners", response_model=RoundWinnersResponse, status_code=status.HTTP_201_CREATED)
def create_round_winners(
    data: RoundWinnersCreate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Create a round winners record for an event.
    Requires admin authentication.
    """
    existing = db.query(RoundWinners).filter(
        RoundWinners.event_id == data.event_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Results already exist for this event. Use PUT to update."
        )

    record = RoundWinners(
        event_id=data.event_id,
        lowest_gross_winner=data.lowest_gross_winner,
        lowest_gross_score=data.lowest_gross_score,
        stableford_winner=data.stableford_winner,
        stableford_points=data.stableford_points,
        straightest_drive_winner=data.straightest_drive_winner,
        straightest_drive_hole=data.straightest_drive_hole,
        straightest_drive_distance=data.straightest_drive_distance,
        close_to_pin=json.dumps([e.dict() for e in (data.close_to_pin or [])]),
        sponsors=json.dumps([s.dict() for s in (data.sponsors or [])]),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.put("/admin/round-winners/{record_id}", response_model=RoundWinnersResponse)
def update_round_winners(
    record_id: int,
    data: RoundWinnersUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Update an existing round winners record.
    Requires admin authentication.
    """
    record = db.query(RoundWinners).filter(
        RoundWinners.id == record_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    if data.lowest_gross_winner is not None:
        record.lowest_gross_winner = data.lowest_gross_winner
    if data.lowest_gross_score is not None:
        record.lowest_gross_score = data.lowest_gross_score
    if data.stableford_winner is not None:
        record.stableford_winner = data.stableford_winner
    if data.stableford_points is not None:
        record.stableford_points = data.stableford_points
    if data.straightest_drive_winner is not None:
        record.straightest_drive_winner = data.straightest_drive_winner
    if data.straightest_drive_hole is not None:
        record.straightest_drive_hole = data.straightest_drive_hole
    if data.straightest_drive_distance is not None:
        record.straightest_drive_distance = data.straightest_drive_distance
    if data.close_to_pin is not None:
        record.close_to_pin = json.dumps([e.dict() for e in data.close_to_pin])
    if data.sponsors is not None:
        record.sponsors = json.dumps([s.dict() for s in data.sponsors])

    db.commit()
    db.refresh(record)

    return record


@router.delete("/admin/round-winners/{record_id}")
def delete_round_winners(
    record_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Delete a round winners record.
    Requires admin authentication.
    """
    record = db.query(RoundWinners).filter(
        RoundWinners.id == record_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    db.delete(record)
    db.commit()

    return {"message": "Record deleted successfully", "id": record_id}