import json
from typing import Optional, List, Tuple, Dict

from sqlalchemy import select, desc, asc
from sqlalchemy.orm import Session, joinedload

from src.models.banner_message import Banner
from src.models.carousel_image import CarouselImage
from src.models.event import Event
from src.models.event_registration import EventRegistration
from src.models.photo_album import PhotoAlbum
from src.models.site_content import SiteContent
from src.models.user import User, UserAccount


class AdminRepository:
    """Repository for admin-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    # User Management
    def get_all_users(self) -> List[Tuple[User, UserAccount]]:
        """Get all users with their accounts."""
        stmt = select(User, UserAccount).join(
            UserAccount, User.user_account_id == UserAccount.id, isouter=True
        )
        result = self.db.execute(stmt).all()
        return [(row[0], row[1]) for row in result]

    def get_user_account_by_id(self, user_id: int) -> Optional[UserAccount]:
        """Get user account by user ID."""
        stmt = select(UserAccount).where(UserAccount.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_user_role(self, user_id: int, role: str) -> Optional[UserAccount]:
        """Update user role."""
        account = self.get_user_account_by_id(user_id)
        if account:
            account.role = role
            self.db.flush()
        return account

    def delete_user(self, user_id: int) -> bool:
        """Delete user and associated account."""
        user = self.db.get(User, user_id)
        if not user:
            return False

        # Use your existing method to get the account
        account = self.get_user_account_by_id(user_id)
        if account:
            self.db.delete(account)

        # Delete event registrations
        self.db.query(EventRegistration).filter(
            EventRegistration.user_id == user_id
        ).delete(synchronize_session=False)

        # Delete the user
        self.db.delete(user)
        self.db.flush()

        return True

    # Event Management
    def get_event_registrations(self, event_id: int) -> List[EventRegistration]:
        """Get all registrations for an event."""

        stmt = (
            select(EventRegistration)
            .options(
                joinedload(EventRegistration.user_account)
                .joinedload(UserAccount.user)
            )
            .where(EventRegistration.event_id == event_id)
        )
        result = self.db.execute(stmt).scalars().unique().all()
        return list(result)

    def create_event(self, event_data: dict) -> Event:
        """Create a new event."""
        event = Event(**event_data)
        self.db.add(event)
        self.db.flush()
        self.db.refresh(event)
        return event

    def update_event(self, event_id: int, event_data: dict) -> Optional[Event]:
        """Update an event."""
        event = self.db.get(Event, event_id)
        if event:
            for key, value in event_data.items():
                if value is not None:
                    setattr(event, key, value)
            self.db.flush()
            self.db.refresh(event)
        return event

    def delete_event(self, event_id: int) -> bool:
        """Delete an event."""
        event = self.db.get(Event, event_id)
        if event:
            self.db.delete(event)
            self.db.flush()
            return True
        return False

    # Banner Management
    def get_all_banners(self) -> List[Banner]:
        """Get all banner messages."""
        stmt = select(Banner)
        return list(self.db.execute(stmt).scalars().all())

    def update_banner_messages(self, messages: List[str]) -> None:
        """Replace all banner messages with new ones."""
        # Delete existing banners
        stmt = select(Banner)
        existing = self.db.execute(stmt).scalars().all()
        for banner in existing:
            self.db.delete(banner)

        # Create new banners
        for message in messages:
            banner = Banner(message=message)
            self.db.add(banner)
        self.db.flush()


    # Photo Album Management
    def get_all_photo_albums(self) -> List[PhotoAlbum]:
        """Get all photo albums."""
        stmt = select(PhotoAlbum).order_by(PhotoAlbum.date.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create_photo_album(self, album_data: dict) -> PhotoAlbum:
        """Create a new photo album."""
        if "images" in album_data and album_data["images"]:
            album_data["images"] = json.dumps(album_data["images"])
        album = PhotoAlbum(**album_data)
        self.db.add(album)
        self.db.flush()
        self.db.refresh(album)
        return album

    def update_photo_album(self, album_id: int, album_data: dict) -> Optional[PhotoAlbum]:
        """Update a photo album."""
        album = self.db.get(PhotoAlbum, album_id)
        if album:
            for key, value in album_data.items():
                if value is not None:
                    if key == "images" and isinstance(value, list):
                        value = json.dumps(value)
                    setattr(album, key, value)
            self.db.flush()
            self.db.refresh(album)
        return album

    def delete_photo_album(self, album_id: int) -> bool:
        """Delete a photo album."""
        album = self.db.get(PhotoAlbum, album_id)
        if album:
            self.db.delete(album)
            self.db.flush()
            return True
        return False

    # Site Content Management
    def get_all_content(self) -> List[SiteContent]:
        """Get all site content."""
        stmt = select(SiteContent)
        return list(self.db.execute(stmt).scalars().all())

    def update_content(self, content_dict: Dict[str, str]) -> None:
        """Update or create site content."""
        for key, value in content_dict.items():
            stmt = select(SiteContent).where(SiteContent.key == key)
            content = self.db.execute(stmt).scalar_one_or_none()
            if content:
                content.value = value
            else:
                content = SiteContent(key=key, value=value)
                self.db.add(content)
        self.db.flush()

    # Carousel Images Management
    def get_carousel_images(self) -> List[CarouselImage]:
        """Get all carousel images ordered by display_order."""
        stmt = select(CarouselImage).order_by(CarouselImage.display_order)
        return list(self.db.execute(stmt).scalars().all())


    def get_all_events(self, order_by: str = 'date', order: str = 'desc') -> List[Event]:
        """Get all events sorted by specified field."""

        stmt = select(Event)

        # Apply ordering
        if order_by == 'date':
            order_col = Event.date
        else:
            order_col = Event.id

        if order == 'desc':
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(asc(order_col))

        result = self.db.execute(stmt).scalars().all()
        return list(result)


    def update_carousel_images(self, images_data: List[dict]) -> List[CarouselImage]:
        """Replace all carousel images with new ones."""
        # Delete existing carousel images
        stmt = select(CarouselImage)
        existing = self.db.execute(stmt).scalars().all()
        for img in existing:
            self.db.delete(img)

        # Create new carousel images
        new_images = []
        for img_data in images_data:
            image = CarouselImage(**img_data)
            self.db.add(image)
            new_images.append(image)
        self.db.flush()

        # Refresh to get IDs
        for img in new_images:
            self.db.refresh(img)

        return new_images

    def commit(self) -> None:
        """Commit the transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self.db.rollback()

    def delete_event_registration(self, registration_id: int) -> bool:
        """
        Delete an event registration.
        Returns True if registration was found and deleted, False otherwise.
        """
        from src.models.event_registration import EventRegistration

        registration = self.db.query(EventRegistration).filter(
            EventRegistration.id == registration_id
        ).first()

        if not registration:
            return False

        self.db.delete(registration)
        self.db.commit()
        return True
