from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.event import Event
from models.event_registration import EventRegistration
from models.user import User, UserAccount
from typing import Optional, List

class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID."""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_account_by_user_id(self, user_id: int) -> Optional[UserAccount]:
        """Retrieve a user account by user ID."""
        stmt = select(UserAccount).where(UserAccount.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_user_handicap(self, user_id: int, handicap: Optional[str]=None) -> Optional[User]:
        """Update a user's handicap."""
        user = self.get_user_by_id(user_id)
        if user:
            user.handicap = handicap
            self.db.commit()
            self.db.refresh(user) 
        return user

    def update_user_password(self, user_id: int, new_password_hash: str) -> None:
        """Update a user's password hash."""
        account = self.get_user_account_by_user_id(user_id)
        if account:
            account.password_hash = new_password_hash
            self.db.flush()

    def get_user_registered_events(self, user_id: int) -> List[EventRegistration]:
        """Get all events a user is registered for."""
        stmt = (
            select(EventRegistration)
            .options(joinedload(EventRegistration.event))
            .where(EventRegistration.user_id == user_id)
        )
        result = self.db.execute(stmt).scalars().all()
        return list(result)

    def create_event_registration(
        self, 
        user_id: int, 
        event_id: int,
        email: str,
        phone: str,
        handicap: Optional[str] = None
    ) -> Optional[EventRegistration]:
        """Create a new event registration for a user."""
        # Check if registration already exists
        existing = self.get_registration_by_user_and_event(user_id, event_id)
        if existing:
            return None

        registration = EventRegistration(
            user_id=user_id, 
            event_id=event_id,
            email=email,
            phone=phone,
            handicap=handicap,
            payment_status="pending"  
        )
        self.db.add(registration)
        self.db.flush()
        return registration

    def get_registration_by_user_and_event(
        self, user_id: int, event_id: int
    ) -> Optional[EventRegistration]:
        """Check if a user is already registered for an event."""
        stmt = select(EventRegistration).where(
            EventRegistration.user_id == user_id, EventRegistration.event_id == event_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Get an event by ID."""
        stmt = select(Event).where(Event.id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()
