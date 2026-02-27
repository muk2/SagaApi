from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from src.core.database import get_db
from src.core.dependencies import OptionalUser
from src.services.event_service import list_events
from src.models.event_registration import EventRegistration
from src.models.guest import Guest
from src.models.user import User, UserAccount
from pydantic import BaseModel, EmailStr
from src.models.event import Event

router = APIRouter(prefix="/api/events", tags=["Events"])


class EventRegistrationRequest(BaseModel):
    """Request schema for event registration (both authenticated and guest users)"""
    event_id: int
    email: EmailStr
    phone: str
    handicap: Optional[str] = None
    
    # ✅ For guest registrations
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.get("/")
def get_events(db: Session = Depends(get_db)):
    return list_events(db)


@router.post("/register")
async def register_for_event(
    data: EventRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: OptionalUser = None  
):
    """
    Register for an event - works for both authenticated users and guests
    """
    
    existing_registration = (
        db.query(EventRegistration)
        .filter(
            EventRegistration.event_id == data.event_id,
            EventRegistration.email == data.email.lower()  # Case-insensitive check
        )
        .first()
    )
    
    if existing_registration:
        raise HTTPException(
            status_code=400,
            detail="You are already registered for this event"
        )
    
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    registration_count = (
        db.query(EventRegistration)
        .filter(EventRegistration.event_id == data.event_id)
        .count()
    )
    
    if registration_count >= event.capacity:
        raise HTTPException(
            status_code=400,
            detail="This event is at full capacity. Registration is closed."
        )
    
    if current_user:
        account = db.query(UserAccount).filter(UserAccount.user_id == current_user.id).first()
        if not account:
            raise HTTPException(status_code=404, detail="User account not found")
        
        user_id = account.id
        
        # Create registration with user_id
        registration = EventRegistration(
            event_id=data.event_id,
            user_id=user_id,
            email=data.email,
            phone=data.phone,
            handicap=data.handicap
        )
    else:
        # ✅ Guest registration - must have first_name and last_name
        if not data.first_name or not data.last_name:
            raise HTTPException(
                status_code=400,
                detail="First name and last name are required for guest registration"
            )
        
        # Create guest record
        guest = Guest(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            handicap_index=data.handicap if data.handicap else 0
        )
        db.add(guest)
        db.flush()  # Get the guest ID
        
        # Create registration with guest_id
        registration = EventRegistration(
            event_id=data.event_id,
            guest_id=guest.id,
            email=data.email,
            phone=data.phone,
            handicap=data.handicap if data.handicap else 0
        )
    
    db.add(registration)
    db.commit()
    db.refresh(registration)
    
    return {
        "message": "Registration successful",
        "registration_id": registration.id
    }