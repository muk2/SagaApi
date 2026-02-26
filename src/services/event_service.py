from sqlalchemy.orm import Session

from repositories.event_repository import get_events
from models.event_registration import EventRegistration

def list_events(db: Session):
    events = get_events(db)
    
    
    result = []
    for event in events:
        registered_count = db.query(EventRegistration)\
            .filter(EventRegistration.event_id == event.id)\
            .count()
        
        # Create a dict with event data plus registered count
        event_dict = {
            'id': event.id,
            'township': event.township,
            'state': event.state,
            'zipcode': event.zipcode,
            'golf_course': event.golf_course,
            'date': event.date,
            'start_time': event.start_time,
            'member_price': float(event.member_price),
            'guest_price': float(event.guest_price),
            'capacity': event.capacity,
            'registered': registered_count,
            'image_url': event.image_url if hasattr(event, 'image_url') else None,
        }
        result.append(event_dict)
    
    return result