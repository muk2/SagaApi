from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.event import (
    EventCreate,
    EventList,
    EventRead,
    EventReadWithTiers,
    EventUpdate,
    PriceTierCreate,
    PriceTierRead,
    PriceTierUpdate,
)
from services.event_service import EventService

router = APIRouter(prefix="/api/events", tags=["Events"])


# ============ Event Endpoints ============


@router.get("/", response_model=EventList)
def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    upcoming_only: bool = Query(False, description="Only return events on or after today"),
    db: Session = Depends(get_db),
) -> EventList:
    """
    List all events with pagination.

    - **skip**: Number of events to skip (for pagination)
    - **limit**: Maximum number of events to return (max 100)
    - **upcoming_only**: If true, only return future events
    """
    service = EventService(db)
    events, total = service.list_events(skip=skip, limit=limit, upcoming_only=upcoming_only)
    return EventList(events=events, total=total)


@router.get("/{event_id}", response_model=EventReadWithTiers)
def get_event(event_id: int, db: Session = Depends(get_db)) -> EventReadWithTiers:
    """
    Get a single event by ID, including its price tiers.
    """
    service = EventService(db)
    return service.get_event_with_tiers(event_id)


@router.post("/", response_model=EventReadWithTiers, status_code=status.HTTP_201_CREATED)
def create_event(data: EventCreate, db: Session = Depends(get_db)) -> EventReadWithTiers:
    """
    Create a new event.

    Optionally include price tiers in the request body to create them
    along with the event.
    """
    service = EventService(db)
    return service.create_event(data)


@router.put("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    data: EventUpdate,
    db: Session = Depends(get_db),
) -> EventRead:
    """
    Update an existing event.

    Only the fields provided will be updated.
    """
    service = EventService(db)
    return service.update_event(event_id, data)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete an event and all its associated price tiers.
    """
    service = EventService(db)
    service.delete_event(event_id)


# ============ Price Tier Endpoints ============


@router.get("/{event_id}/price-tiers", response_model=list[PriceTierRead])
def get_event_price_tiers(
    event_id: int,
    active_only: bool = Query(False, description="Only return active price tiers"),
    db: Session = Depends(get_db),
) -> list[PriceTierRead]:
    """
    Get all price tiers for an event.
    """
    service = EventService(db)
    return service.get_event_price_tiers(event_id, active_only=active_only)


@router.post(
    "/{event_id}/price-tiers",
    response_model=PriceTierRead,
    status_code=status.HTTP_201_CREATED,
)
def create_price_tier(
    event_id: int,
    data: PriceTierCreate,
    db: Session = Depends(get_db),
) -> PriceTierRead:
    """
    Create a new price tier for an event.
    """
    service = EventService(db)
    return service.create_price_tier(event_id, data)


@router.put("/price-tiers/{tier_id}", response_model=PriceTierRead)
def update_price_tier(
    tier_id: int,
    data: PriceTierUpdate,
    db: Session = Depends(get_db),
) -> PriceTierRead:
    """
    Update an existing price tier.

    Only the fields provided will be updated.
    """
    service = EventService(db)
    return service.update_price_tier(tier_id, data)


@router.delete("/price-tiers/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price_tier(tier_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a price tier.
    """
    service = EventService(db)
    service.delete_price_tier(tier_id)
