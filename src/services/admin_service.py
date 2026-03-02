import json
import os
from datetime import datetime, time
from typing import Optional, List, Tuple, Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.admin_repository import AdminRepository
from schemas.admin import (
    CarouselImageItem,
    ContentItem,
    EventRegistrationDetail,
    PhotoAlbumResponse,
    UserListItem,
    EventResponse
)

from repositories.carousel_repository import CarouselRepository
from models.event_registration import EventRegistration
from models.photo_album import PhotoAlbum
from repositories.partner_repository import PartnerRepository
from schemas.partner import PartnerResponse
from models.event import Event
from models.user import User, UserAccount
from models.guest import Guest


class AdminService:
    """Service layer for admin-related business logic."""

    def __init__(self, db: Session):
        self.repo = AdminRepository(db)

    # User Management
    def get_all_users(self) -> List[UserListItem]:
        """Get all users with their account info."""
        users_data = self.repo.get_all_users()
        result = []
        for user, account in users_data:
            result.append(
                UserListItem(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=account.email if account else "",
                    role=account.role if account else None,
                    phone_number=user.phone_number,
                    handicap=user.handicap,
                    last_logged_in=account.last_logged_in if account else None,
                    membership=str(user.membership)
                )
            )
        return result

    def update_user_role(self, user_id: int, role: str) -> Tuple[int, str]:
        """Update a user's role."""
        try:
            account = self.repo.update_user_role(user_id, role)
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User account not found",
                )
            self.repo.commit()
            return user_id, role
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user role: {e!s}",
            ) from e

    def delete_user(self, user_id: int) -> None:
        """Delete a user and their account."""
        try:
            deleted = self.repo.delete_user(user_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            self.repo.commit()
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {e!s}",
            ) from e

    def get_event_registrations(self, event_id: int) -> List[EventRegistrationDetail]:
        """Get all registrations for an event with membership info."""

        registrations = (
            self.repo.db.query(EventRegistration)
            .outerjoin(UserAccount, EventRegistration.user_id == UserAccount.id)
            .outerjoin(User, UserAccount.user_id == User.id)
            .outerjoin(Guest, EventRegistration.guest_id == Guest.id)
            .filter(EventRegistration.event_id == event_id)
            .all()
        )

        result = []

        for reg in registrations:
            user_name = None
            membership = "guest"

            if reg.user_account and reg.user_account.user:
                user = reg.user_account.user
                user_name = f"{user.first_name} {user.last_name}"
                membership = getattr(user, 'membership', 'guest') or 'guest'

            elif reg.guest:
                guest = reg.guest
                user_name = f"{guest.first_name} {guest.last_name}"
                membership = "guest"

            result.append(
                EventRegistrationDetail(
                    id=reg.id,
                    user_name=user_name,
                    email=reg.email,
                    phone=reg.phone,
                    handicap=str(reg.handicap) if reg.handicap else None,
                    created_at=reg.created_at.isoformat() if reg.created_at else None,
                    payment_status='Paid',
                    membership=membership,
                    is_sponsor=reg.is_sponsor or False,
                    sponsor_amount=float(reg.sponsor_amount) if reg.sponsor_amount else None,
                    company_name=reg.company_name,
                )
            )

        return result

    def delete_event_registration(self, registration_id: int) -> bool:
        """
        Delete an event registration by ID.
        Returns True if deleted, False if not found.
        """
        return self.repo.delete_event_registration(registration_id)

    def get_all_events(self, sort_by: str = 'date', sort_order: str = 'asc') -> List[EventResponse]:
        """Get all events with registration counts."""
        events = self.repo.get_all_events(sort_by, sort_order)
        result = []

        for event in events:
            registered_count = self.repo.db.query(EventRegistration)\
                .filter(EventRegistration.event_id == event.id)\
                .count()

            result.append(
                EventResponse(
                    id=event.id,
                    golf_course=event.golf_course,
                    township=event.township,
                    state=event.state,
                    zipcode=getattr(event, 'zipcode', None),
                    date=event.date.strftime('%Y-%m-%d') if hasattr(event.date, 'strftime') else str(event.date),
                    start_time=str(event.start_time),
                    guest_price=float(event.guest_price),
                    member_price=float(event.member_price) if event.member_price else float(event.guest_price),
                    capacity=event.capacity,
                    registered=registered_count,
                    image_url=getattr(event, 'image_url', None),
                    description=getattr(event, 'description', None),
                )
            )

        return result

    # Event Management
    def create_event(self, event_data: dict) -> dict:
        """Create a new event."""
        try:
            if "start_time" in event_data and isinstance(event_data["start_time"], str):
                time_parts = event_data["start_time"].split(":")
                event_data["start_time"] = time(
                    int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0
                )

            event = self.repo.create_event(event_data)
            self.repo.commit()
            return {
                "id": event.id,
                "township": event.township,
                "state": event.state,
                "zipcode": event.zipcode,
                "golf_course": event.golf_course,
                "date": event.date,
                "start_time": str(event.start_time),
                "member_price": event.member_price,
                "guest_price": event.guest_price,
                "capacity": event.capacity,
                "image_url": getattr(event, 'image_url', None),
                "description": getattr(event, 'description', None),
            }
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create event: {e!s}",
            ) from e

    def update_event(self, event_id: int, event_data: dict) -> Optional[dict]:
        """Update an event and delete old image if replaced."""
        try:
            event = self.repo.db.query(Event).filter(Event.id == event_id).first()
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found",
                )

            old_image_url = event.image_url if hasattr(event, 'image_url') else None
            new_image_url = event_data.get('image_url')

            if new_image_url and old_image_url and new_image_url != old_image_url:
                if old_image_url.startswith('/uploads/'):
                    file_path = old_image_url.lstrip('/')
                    full_path = os.path.join(os.getcwd(), file_path)
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            print(f"Deleted old event image: {full_path}")
                    except Exception as e:
                        print(f"Failed to delete old file {full_path}: {e}")

            if "start_time" in event_data and isinstance(event_data["start_time"], str):
                time_parts = event_data["start_time"].split(":")
                event_data["start_time"] = time(
                    int(time_parts[0]), int(time_parts[1]), int(time_parts[2]) if len(time_parts) > 2 else 0
                )

            event = self.repo.update_event(event_id, event_data)
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found",
                )
            self.repo.commit()
            return {
                "id": event.id,
                "township": event.township,
                "state": event.state,
                "zipcode": event.zipcode,
                "golf_course": event.golf_course,
                "date": event.date,
                "start_time": str(event.start_time),
                "member_price": event.member_price,
                "guest_price": event.guest_price,
                "capacity": event.capacity,
                "image_url": getattr(event, 'image_url', None),
                "description": getattr(event, 'description', None),
            }
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update event: {e!s}",
            ) from e

    def delete_event(self, event_id: int) -> None:
        """Delete an event and its associated image file."""
        try:
            event = self.repo.db.query(Event).filter(Event.id == event_id).first()
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found",
                )

            if hasattr(event, 'image_url') and event.image_url and event.image_url.startswith('/uploads/'):
                file_path = event.image_url.lstrip('/')
                full_path = os.path.join(os.getcwd(), file_path)
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"Deleted event image: {full_path}")
                except Exception as e:
                    print(f"Failed to delete file {full_path}: {e}")

            deleted = self.repo.delete_event(event_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found",
                )
            self.repo.commit()
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete event: {e!s}",
            ) from e

    # Banner Management
    def update_banner_messages(self, messages: List[str]) -> None:
        """Update all banner messages."""
        try:
            self.repo.update_banner_messages(messages)
            self.repo.commit()
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update banner messages: {e!s}",
            ) from e

    def get_banner_settings(self) -> dict:
        """Get current banner settings."""
        settings = self.repo.get_banner_settings()
        if not settings:
            return {"enabled": False, "messages": []}
        return {
            "enabled": settings.enabled,
            "messages": settings.messages or []
        }

    def update_banner_settings(self, enabled: bool, messages: Optional[List[str]] = None) -> None:
        """Update banner settings."""
        try:
            self.repo.update_banner_settings(enabled, messages)
            self.repo.commit()
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update banner settings: {e!s}",
            ) from e

    # Photo Album Management
    def get_all_photo_albums(self) -> List[PhotoAlbum]:
        """Get all photo albums."""
        return self.repo.get_all_photo_albums()

    def create_photo_album(self, album_data: dict) -> PhotoAlbum:
        """Create a new photo album."""
        album = self.repo.create_photo_album(album_data)
        self.repo.commit()
        self.repo.db.refresh(album)
        return album

    def update_photo_album(self, album_id: int, album_data: dict) -> PhotoAlbumResponse:
        """Update photo album and delete old cover image if replaced."""
        album = self.repo.db.query(PhotoAlbum).filter(PhotoAlbum.id == album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")

        old_cover_image = album.cover_image
        new_cover_image = album_data.get('cover_image')

        if new_cover_image and old_cover_image and new_cover_image != old_cover_image:
            if old_cover_image.startswith('/uploads/'):
                file_path = old_cover_image.lstrip('/')
                full_path = os.path.join(os.getcwd(), file_path)
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"Deleted old album cover: {full_path}")
                except Exception as e:
                    print(f"Failed to delete old file {full_path}: {e}")

        updated_album = self.repo.update_photo_album(album_id, album_data)
        self.repo.db.commit()
        self.repo.db.refresh(updated_album)
        return updated_album

    def delete_photo_album(self, album_id: int) -> None:
        """Delete photo album and its cover image."""
        album = self.repo.db.query(PhotoAlbum).filter(PhotoAlbum.id == album_id).first()
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")

        if album.cover_image and album.cover_image.startswith('/uploads/'):
            file_path = album.cover_image.lstrip('/')
            full_path = os.path.join(os.getcwd(), file_path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"Failed to delete file {full_path}: {e}")

        self.repo.db.delete(album)
        self.repo.db.commit()

    # Site Content Management
    def get_all_content(self) -> List[ContentItem]:
        """Get all site content."""
        content_list = self.repo.get_all_content()
        return [
            ContentItem(key=c.key, value=c.value, description=c.description) for c in content_list
        ]

    def update_content(self, content_dict: Dict[str, str]) -> None:
        """Update site content."""
        try:
            self.repo.update_content(content_dict)
            self.repo.commit()
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update content: {e!s}",
            ) from e

    # Carousel Images Management
    def update_carousel_images(self, image_urls: List[str]) -> List[str]:
        """Update carousel images - accepts list of URL strings."""
        carousel_repo = CarouselRepository(self.repo.db)
        carousel_repo.update_images(image_urls)
        return image_urls

    def get_carousel_images(self) -> List[str]:
        """Get carousel images - returns list of URL strings."""
        carousel_repo = CarouselRepository(self.repo.db)
        return carousel_repo.get_all_images()

    # Partner Management
    def get_all_partners(self) -> List[PartnerResponse]:
        """Get all partners."""
        partner_repo = PartnerRepository(self.repo.db)
        partners = partner_repo.get_all()
        return [
            PartnerResponse(
                id=p.id,
                name=p.name,
                logo_url=p.logo_url,
                website_url=p.website_url,
                display_order=p.display_order
            )
            for p in partners
        ]

    def create_partner(self, name: str, logo_url: str, website_url: str, display_order: int) -> PartnerResponse:
        """Create new partner."""
        partner_repo = PartnerRepository(self.repo.db)
        partner = partner_repo.create(
            name=name,
            logo_url=logo_url,
            website_url=website_url,
            display_order=display_order
        )
        return PartnerResponse(
            id=partner.id,
            name=partner.name,
            logo_url=partner.logo_url,
            website_url=partner.website_url,
            display_order=partner.display_order
        )

    def update_partner(self, partner_id: int, **kwargs) -> PartnerResponse:
        """Update partner and delete old logo if replaced."""
        partner_repo = PartnerRepository(self.repo.db)

        partner = partner_repo.get_by_id(partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")

        old_logo_url = partner.logo_url
        new_logo_url = kwargs.get('logo_url')

        if new_logo_url and old_logo_url and new_logo_url != old_logo_url:
            if old_logo_url.startswith('/uploads/'):
                file_path = old_logo_url.lstrip('/')
                full_path = os.path.join(os.getcwd(), file_path)
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"Deleted old partner logo: {full_path}")
                except Exception as e:
                    print(f"Failed to delete old file {full_path}: {e}")

        updated_partner = partner_repo.update(partner_id, **kwargs)
        if not updated_partner:
            raise HTTPException(status_code=404, detail="Partner not found")

        return PartnerResponse(
            id=updated_partner.id,
            name=updated_partner.name,
            logo_url=updated_partner.logo_url,
            website_url=updated_partner.website_url,
            display_order=updated_partner.display_order
        )

    def delete_partner(self, partner_id: int) -> bool:
        """Delete partner and its logo file."""
        partner_repo = PartnerRepository(self.repo.db)

        partner = partner_repo.get_by_id(partner_id)
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")

        if partner.logo_url and partner.logo_url.startswith('/uploads/'):
            file_path = partner.logo_url.lstrip('/')
            full_path = os.path.join(os.getcwd(), file_path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
            except Exception as e:
                print(f"Failed to delete file {full_path}: {e}")

        success = partner_repo.delete(partner_id)
        if not success:
            raise HTTPException(status_code=404, detail="Partner not found")

        return success