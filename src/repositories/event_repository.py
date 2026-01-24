from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.event import Event, EventPriceTier


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        upcoming_only: bool = False,
    ) -> list[Event]:
        stmt = select(Event)
        if upcoming_only:
            stmt = stmt.where(Event.date >= date.today())
        stmt = stmt.order_by(Event.date).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self, upcoming_only: bool = False) -> int:
        stmt = select(Event)
        if upcoming_only:
            stmt = stmt.where(Event.date >= date.today())
        return len(list(self.db.execute(stmt).scalars().all()))

    def get_by_id(self, event_id: int) -> Event | None:
        stmt = select(Event).where(Event.id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_with_tiers(self, event_id: int) -> Event | None:
        stmt = select(Event).options(joinedload(Event.price_tiers)).where(Event.id == event_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.flush()
        return event

    def update(self, event: Event, updates: dict) -> Event:
        for key, value in updates.items():
            if value is not None:
                setattr(event, key, value)
        self.db.flush()
        return event

    def delete(self, event: Event) -> None:
        self.db.delete(event)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()


class PriceTierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_event_id(self, event_id: int, active_only: bool = False) -> list[EventPriceTier]:
        stmt = select(EventPriceTier).where(EventPriceTier.event_id == event_id)
        if active_only:
            stmt = stmt.where(EventPriceTier.is_active.is_(True))
        return list(self.db.execute(stmt).scalars().all())

    def get_by_id(self, tier_id: int) -> EventPriceTier | None:
        stmt = select(EventPriceTier).where(EventPriceTier.id == tier_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, tier: EventPriceTier) -> EventPriceTier:
        self.db.add(tier)
        self.db.flush()
        return tier

    def update(self, tier: EventPriceTier, updates: dict) -> EventPriceTier:
        for key, value in updates.items():
            if value is not None:
                setattr(tier, key, value)
        self.db.flush()
        return tier

    def delete(self, tier: EventPriceTier) -> None:
        self.db.delete(tier)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
