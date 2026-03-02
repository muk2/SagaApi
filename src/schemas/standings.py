import json
from typing import List, Optional
from pydantic import BaseModel, field_validator


# ===================================================================
# Leaderboard PDF schemas
# ===================================================================

class LeaderboardPdfResponse(BaseModel):
    id: int
    url: str

    class Config:
        from_attributes = True


# ===================================================================
# Sponsor entry schema
# ===================================================================

class SponsorEntry(BaseModel):
    sponsor_name: Optional[str] = None
    company_name: Optional[str] = None


# ===================================================================
# Close to Pin entry schema
# ===================================================================

class CtpEntry(BaseModel):
    hole: Optional[str] = None
    winner: Optional[str] = None
    distance: Optional[str] = None


# ===================================================================
# Round Winners schemas
# ===================================================================

class RoundWinnersCreate(BaseModel):
    event_id: int
    lowest_gross_winner: Optional[str] = None
    lowest_gross_score: Optional[float] = None
    stableford_winner: Optional[str] = None
    stableford_points: Optional[float] = None
    straightest_drive_winner: Optional[str] = None
    straightest_drive_hole: Optional[str] = None
    straightest_drive_distance: Optional[str] = None
    close_to_pin: Optional[List[CtpEntry]] = []
    sponsors: Optional[List[SponsorEntry]] = []


class RoundWinnersUpdate(BaseModel):
    lowest_gross_winner: Optional[str] = None
    lowest_gross_score: Optional[float] = None
    stableford_winner: Optional[str] = None
    stableford_points: Optional[float] = None
    straightest_drive_winner: Optional[str] = None
    straightest_drive_hole: Optional[str] = None
    straightest_drive_distance: Optional[str] = None
    close_to_pin: Optional[List[CtpEntry]] = None
    sponsors: Optional[List[SponsorEntry]] = None


class RoundWinnersResponse(BaseModel):
    id: int
    event_id: int
    lowest_gross_winner: Optional[str]
    lowest_gross_score: Optional[float]
    stableford_winner: Optional[str]
    stableford_points: Optional[float]
    straightest_drive_winner: Optional[str]
    straightest_drive_hole: Optional[str]
    straightest_drive_distance: Optional[str]
    close_to_pin: Optional[list]
    sponsors: Optional[list]

    @field_validator('close_to_pin', 'sponsors', mode='before')
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return []
        return v or []

    class Config:
        from_attributes = True