from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.event import Event, EventPriceTier
from repositories.event_repository import EventRepository, PriceTierRepository
from schemas.event import EventCreate, EventUpdate, PriceTierCreate, PriceTierUpdate


class EventService:
    def __init__(self, db: Session):
        self.event_repo = EventRepository(db)
        self.tier_repo = PriceTierRepository(db)

    def list_events(
        self,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = False,
    ) -> tuple[list[Event], int]:
        events = self.event_repo.get_all(skip=skip, limit=limit, upcoming_only=upcoming_only)
        total = self.event_repo.count(upcoming_only=upcoming_only)
        return events, total

    def get_event(self, event_id: int) -> Event:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id {event_id} not found",
            )
        return event

    def get_event_with_tiers(self, event_id: int) -> Event:
        event = self.event_repo.get_by_id_with_tiers(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with id {event_id} not found",
            )
        return event

    def create_event(self, data: EventCreate) -> Event:
        try:
            event = Event(
                date=data.date,
                township=data.township,
                state=data.state,
                zipcode=data.zipcode,
                golf_course=data.golf_course,
                start_time=data.start_time,
            )
            self.event_repo.create(event)

            if data.price_tiers:
                for tier_data in data.price_tiers:
                    tier = EventPriceTier(
                        event_id=event.id,
                        tier_name=tier_data.tier_name,
                        price=tier_data.price,
                        description=tier_data.description,
                        is_active=tier_data.is_active,
                    )
                    self.tier_repo.create(tier)

            self.event_repo.commit()
            return self.event_repo.get_by_id_with_tiers(event.id)
        except Exception as e:
            self.event_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create event: {e!s}",
            ) from e

    def update_event(self, event_id: int, data: EventUpdate) -> Event:
        event = self.get_event(event_id)
        try:
            updates = data.model_dump(exclude_unset=True)
            self.event_repo.update(event, updates)
            self.event_repo.commit()
            return event
        except Exception as e:
            self.event_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update event: {e!s}",
            ) from e

    def delete_event(self, event_id: int) -> None:
        event = self.get_event(event_id)
        try:
            self.event_repo.delete(event)
            self.event_repo.commit()
        except Exception as e:
            self.event_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete event: {e!s}",
            ) from e

    # ============ Price Tier Methods ============

    def get_event_price_tiers(
        self, event_id: int, active_only: bool = False
    ) -> list[EventPriceTier]:
        self.get_event(event_id)
        return self.tier_repo.get_by_event_id(event_id, active_only=active_only)

    def create_price_tier(self, event_id: int, data: PriceTierCreate) -> EventPriceTier:
        self.get_event(event_id)
        try:
            tier = EventPriceTier(
                event_id=event_id,
                tier_name=data.tier_name,
                price=data.price,
                description=data.description,
                is_active=data.is_active,
            )
            self.tier_repo.create(tier)
            self.tier_repo.commit()
            return tier
        except Exception as e:
            self.tier_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create price tier: {e!s}",
            ) from e

    def update_price_tier(self, tier_id: int, data: PriceTierUpdate) -> EventPriceTier:
        tier = self.tier_repo.get_by_id(tier_id)
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price tier with id {tier_id} not found",
            )
        try:
            updates = data.model_dump(exclude_unset=True)
            self.tier_repo.update(tier, updates)
            self.tier_repo.commit()
            return tier
        except Exception as e:
            self.tier_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update price tier: {e!s}",
            ) from e

    def delete_price_tier(self, tier_id: int) -> None:
        tier = self.tier_repo.get_by_id(tier_id)
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price tier with id {tier_id} not found",
            )
        try:
            self.tier_repo.delete(tier)
            self.tier_repo.commit()
        except Exception as e:
            self.tier_repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete price tier: {e!s}",
            ) from e
