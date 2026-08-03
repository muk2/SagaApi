import io
import json
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AdminUser
from models.leaderboard_entry import LeaderboardEntry
from models.leaderboard_pdf import LeaderboardPdf
from models.round_winners import RoundWinners
from schemas.standings import (
    LeaderboardEntryResponse,
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
# LEADERBOARD ENTRIES (XLS UPLOAD) ENDPOINTS
# ===================================================================

@router.get("/leaderboard/entries", response_model=List[LeaderboardEntryResponse])
def get_leaderboard_entries(db: Session = Depends(get_db)):
    """Return all leaderboard entries ordered by position."""
    entries = (
        db.query(LeaderboardEntry)
        .order_by(LeaderboardEntry.position)
        .all()
    )
    return entries


@router.post("/admin/leaderboard/upload-xls", response_model=List[LeaderboardEntryResponse], status_code=status.HTTP_201_CREATED)
def upload_leaderboard_xls(
    file: UploadFile = File(...),
    admin_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    """
    Parse an XLS/XLSX/CSV file and upsert leaderboard entries.
    XLS/XLSX: Pos., Player (Last, First), Stableford Points, Total Gross
    CSV: Rank, Player (Last, First), Best 5 Total
    """
    import csv as csv_module

    filename = (file.filename or "").lower()
    is_csv = filename.endswith(".csv")
    is_xls = filename.endswith(".xls") or filename.endswith(".xlsx")

    if not is_csv and not is_xls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .xls, .xlsx, or .csv files are accepted.",
        )

    try:
        contents = file.file.read()
        rows: list[tuple] = []

        if is_csv:
            import io as _io
            text = contents.decode("utf-8-sig")  # strip BOM if present
            reader = csv_module.reader(_io.StringIO(text))
            rows = [tuple(row) for row in reader]
        else:
            # Try openpyxl first (.xlsx), fall back to xlrd (.xls)
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                wb.close()
            except Exception:
                try:
                    import xlrd
                    wb_xls = xlrd.open_workbook(file_contents=contents)
                    ws_xls = wb_xls.sheet_by_index(0)
                    rows = [
                        tuple(ws_xls.cell_value(r, c) for c in range(ws_xls.ncols))
                        for r in range(ws_xls.nrows)
                    ]
                except ImportError:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="xlrd is not installed on the server.",
                    )

        if not rows:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty.")

        # Find header row — look for a row containing "Pos", "Rank", or "Player"
        header_idx = 0
        for i, row in enumerate(rows):
            cells = [str(c).strip().lower() if c else "" for c in row]
            if any(c in ("pos", "rank", "player") or "pos" in c or "player" in c for c in cells):
                header_idx = i
                break

        headers = [str(c).strip().lower() if c else "" for c in rows[header_idx]]

        # Map column indices — support both XLS ("pos.", "stableford points") and CSV ("rank", "best 5 total")
        pos_col = next((i for i, h in enumerate(headers) if "pos" in h or h == "rank"), None)
        player_col = next((i for i, h in enumerate(headers) if "player" in h), None)
        stableford_col = next((i for i, h in enumerate(headers) if "stableford" in h or "best 5" in h), None)
        gross_col = next((i for i, h in enumerate(headers) if "gross" in h), None)

        if pos_col is None or player_col is None or stableford_col is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not find required columns. Expected Rank/Pos., Player, and Best 5 Total/Stableford Points. "
                       f"Found headers: {headers}",
            )

        entries = []
        for row in rows[header_idx + 1:]:
            pos_val = row[pos_col] if pos_col < len(row) else None
            player_val = row[player_col] if player_col < len(row) else None
            stab_val = row[stableford_col] if stableford_col < len(row) else None

            if not pos_val or not player_val:
                continue

            # Parse position (xlrd may return floats like 1.0 for integers)
            try:
                position = int(float(pos_val))
            except (ValueError, TypeError):
                continue

            # Parse player name — expected "Last, First" or "Last First"
            player_str = str(player_val).strip()
            if "," in player_str:
                parts = [p.strip() for p in player_str.split(",", 1)]
                last_name = parts[0]
                first_name = parts[1] if len(parts) > 1 else ""
            else:
                parts = player_str.split(None, 1)
                last_name = parts[0]
                first_name = parts[1] if len(parts) > 1 else ""

            # Parse stableford points
            try:
                stableford_points = float(stab_val) if stab_val is not None else 0
            except (ValueError, TypeError):
                stableford_points = 0

            # Parse total gross (optional)
            total_gross = None
            if gross_col is not None and gross_col < len(row) and row[gross_col] is not None:
                try:
                    total_gross = float(row[gross_col])
                except (ValueError, TypeError):
                    pass

            entries.append(LeaderboardEntry(
                position=position,
                first_name=first_name,
                last_name=last_name,
                stableford_points=stableford_points,
                total_gross=total_gross,
            ))

        if not entries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid player rows found in the spreadsheet.",
            )

        # Upsert: update existing players by name, insert new ones, keep players not in file
        existing = {
            (e.first_name.strip().lower(), e.last_name.strip().lower()): e
            for e in db.query(LeaderboardEntry).all()
        }
        for entry in entries:
            key = (entry.first_name.strip().lower(), entry.last_name.strip().lower())
            if key in existing:
                existing[key].position = entry.position
                existing[key].stableford_points = entry.stableford_points
                existing[key].total_gross = entry.total_gross
            else:
                db.add(entry)
        db.commit()

        # Re-query to get IDs
        result = (
            db.query(LeaderboardEntry)
            .order_by(LeaderboardEntry.position)
            .all()
        )
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse spreadsheet: {exc}",
        )


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
