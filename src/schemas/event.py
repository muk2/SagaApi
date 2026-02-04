from pydantic import BaseModel, field_serializer
from datetime import date as dt_date
from datetime import time as dt_time

class EventRead(BaseModel):
    id: int
    township: str
    state: str
    zipcode: str
    golf_course: str
    date: dt_date
    start_time: dt_time
    member_price: float
    guest_price: float

    class Config:
        from_attributes = True  # Pydantic v2 (ORM mode)

    @field_serializer('date')
    def serialize_date(self, date_val: dt_date, _info):
        return date_val.strftime("%m/%d/%Y") 
