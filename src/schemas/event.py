import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

# ============ Price Tier Schemas ============


class PriceTierBase(BaseModel):
    tier_name: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., ge=0)
    description: str | None = None
    is_active: bool = True


class PriceTierCreate(PriceTierBase):
    pass


class PriceTierUpdate(BaseModel):
    tier_name: str | None = Field(None, min_length=1, max_length=100)
    price: Decimal | None = Field(None, ge=0)
    description: str | None = None
    is_active: bool | None = None


class PriceTierRead(PriceTierBase):
    id: int
    event_id: int

    model_config = {"from_attributes": True}


# ============ Event Schemas ============


class EventBase(BaseModel):
    date: datetime.date
    township: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zipcode: int = Field(..., ge=10000, le=99999)
    golf_course: str = Field(..., min_length=1, max_length=200)
    start_time: datetime.time | None = None


class EventCreate(EventBase):
    price_tiers: list[PriceTierCreate] | None = None


class EventUpdate(BaseModel):
    date: datetime.date | None = None
    township: str | None = Field(None, min_length=1, max_length=100)
    state: str | None = Field(None, min_length=2, max_length=50)
    zipcode: int | None = Field(None, ge=10000, le=99999)
    golf_course: str | None = Field(None, min_length=1, max_length=200)
    start_time: datetime.time | None = None


class EventRead(EventBase):
    id: int

    model_config = {"from_attributes": True}


class EventReadWithTiers(EventRead):
    price_tiers: list[PriceTierRead] = []


class EventList(BaseModel):
    events: list[EventRead]
    total: int
