from pydantic import BaseModel
from datetime import date as dt_date
from datetime import time as dt_time

class BannerRead(BaseModel):
    id: int
    message: str

    class Config:
        from_attributes = True  # Pydantic v2 (ORM mode)