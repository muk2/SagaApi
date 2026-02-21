from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.banner_message import Banner
from models.event import Event
from models.event_registration import EventRegistration
from models.user import User, UserAccount


class AdminRepository:
    """Repository for admin-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    # ── User Operations ───────────────────────────────────────────────────

    def get_all_users(self) -> list[User]:
        """Retrieve all users with their accounts eagerly loaded."""
        stmt = select(User).options(joinedload(User.account))
        return list(self.db.execute(stmt).scalars().unique().all())

    def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by ID with account eagerly loaded."""
        stmt = select(User).options(joinedload(User.account)).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_account_by_user_id(self, user_id: int) -> UserAccount | None:
        """Retrieve a user account by user ID."""
        stmt = select(UserAccount).where(UserAccount.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_user_role(self, account: UserAccount, role: str) -> None:
        """Update a user account's role."""
        account.role = role

    def delete_user_account(self, account: UserAccount) -> None:
        """Delete a user account."""
        self.db.delete(account)

    def delete_user(self, user: User) -> None:
        """Delete a user."""
        self.db.delete(user)

    # ── Event Operations ──────────────────────────────────────────────────

    def get_event_by_id(self, event_id: int) -> Event | None:
        """Retrieve an event by ID."""
        stmt = select(Event).where(Event.id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_event(
        self,
        township: str,
        state: str,
        zipcode: str,
        golf_course: str,
        date,
        start_time,
    ) -> Event:
        """Create a new event."""
        event = Event(
            township=township,
            state=state,
            zipcode=zipcode,
            golf_course=golf_course,
            date=date,
            start_time=start_time,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def delete_event(self, event: Event) -> None:
        """Delete an event."""
        self.db.delete(event)

    def get_event_registrations(self, event_id: int) -> list[EventRegistration]:
        """Retrieve all registrations for a given event."""
        stmt = select(EventRegistration).where(EventRegistration.event_id == event_id)
        return list(self.db.execute(stmt).scalars().all())

    # ── Banner Operations ─────────────────────────────────────────────────

    def get_all_banners(self) -> list[Banner]:
        """Retrieve all banner messages."""
        stmt = select(Banner)
        return list(self.db.execute(stmt).scalars().all())

    def delete_all_banners(self) -> None:
        """Delete all banner messages."""
        banners = self.get_all_banners()
        for banner in banners:
            self.db.delete(banner)

    def create_banner(self, message: str) -> Banner:
        """Create a new banner message."""
        banner = Banner(message=message)
        self.db.add(banner)
        self.db.flush()
        return banner

    # ── Transaction Management ────────────────────────────────────────────

    def commit(self) -> None:
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.db.rollback()
