from pydantic import BaseModel


class EventRead(BaseModel):
    id: int
    township: str
    golf_course: str

    class Config:
        from_attributes = True   # Pydantic v2 (ORM mode)