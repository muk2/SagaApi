import json
from datetime import datetime, time
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.admin_repository import AdminRepository
from schemas.admin import (
    CarouselImageItem,
    ContentItem,
    EventRegistrationDetail,
    PhotoAlbumResponse,
    UserListItem,
)


class AdminService:
    """Service layer for admin-related business logic."""

    def __init__(self, db: Session):
        self.repo = AdminRepository(db)

    # User Management
    def get_all_users(self) -> list[UserListItem]:
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
                )
            )
        return result

    def update_user_role(self, user_id: int, role: str) -> tuple[int, str]:
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

    def get_event_registrations(self, event_id: int) -> list[EventRegistrationDetail]:
        """Get all registrations for an event."""
        registrations = self.repo.get_event_registrations(event_id)
        result = []
        for reg in registrations:
            user_name = None
            if reg.user:
                user_name = f"{reg.user.first_name} {reg.user.last_name}"

            result.append(
                EventRegistrationDetail(
                    id=reg.id,
                    user_id=reg.user_id,
                    guest_id=reg.guest_id,
                    email=reg.email,
                    phone=reg.phone,
                    handicap=reg.handicap,
                    payment_status=reg.payment_status,
                    payment_method=reg.payment_method,
                    amount_paid=float(reg.amount_paid) if reg.amount_paid else None,
                    created_at=reg.created_at,
                    user_name=user_name,
                )
            )
        return result

    # Event Management
    def create_event(self, event_data: dict) -> dict:
        """Create a new event."""
        try:
            # Convert start_time string to time object if needed
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
            }
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create event: {e!s}",
            ) from e

    def update_event(self, event_id: int, event_data: dict) -> Optional[dict]:
        """Update an event."""
        try:
            # Convert start_time string to time object if needed
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
        """Delete an event."""
        try:
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
    def update_banner_messages(self, messages: list[str]) -> None:
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

    # Photo Album Management
    def get_all_photo_albums(self) -> list[PhotoAlbumResponse]:
        """Get all photo albums."""
        albums = self.repo.get_all_photo_albums()
        result = []
        for album in albums:
            images = None
            if album.images:
                try:
                    images = json.loads(album.images)
                except json.JSONDecodeError:
                    images = None

            result.append(
                PhotoAlbumResponse(
                    id=album.id,
                    title=album.title,
                    description=album.description,
                    cover_image_url=album.cover_image_url,
                    images=images,
                    created_at=album.created_at,
                    updated_at=album.updated_at,
                )
            )
        return result

    def create_photo_album(self, album_data: dict) -> PhotoAlbumResponse:
        """Create a new photo album."""
        try:
            album = self.repo.create_photo_album(album_data)
            self.repo.commit()

            images = None
            if album.images:
                try:
                    images = json.loads(album.images)
                except json.JSONDecodeError:
                    images = None

            return PhotoAlbumResponse(
                id=album.id,
                title=album.title,
                description=album.description,
                cover_image_url=album.cover_image_url,
                images=images,
                created_at=album.created_at,
                updated_at=album.updated_at,
            )
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create photo album: {e!s}",
            ) from e

    def update_photo_album(self, album_id: int, album_data: dict) -> PhotoAlbumResponse:
        """Update a photo album."""
        try:
            album = self.repo.update_photo_album(album_id, album_data)
            if not album:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Photo album not found",
                )
            self.repo.commit()

            images = None
            if album.images:
                try:
                    images = json.loads(album.images)
                except json.JSONDecodeError:
                    images = None

            return PhotoAlbumResponse(
                id=album.id,
                title=album.title,
                description=album.description,
                cover_image_url=album.cover_image_url,
                images=images,
                created_at=album.created_at,
                updated_at=album.updated_at,
            )
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update photo album: {e!s}",
            ) from e

    def delete_photo_album(self, album_id: int) -> None:
        """Delete a photo album."""
        try:
            deleted = self.repo.delete_photo_album(album_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Photo album not found",
                )
            self.repo.commit()
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete photo album: {e!s}",
            ) from e

    # Site Content Management
    def get_all_content(self) -> list[ContentItem]:
        """Get all site content."""
        content_list = self.repo.get_all_content()
        return [
            ContentItem(key=c.key, value=c.value, description=c.description) for c in content_list
        ]

    def update_content(self, content_dict: dict[str, str]) -> None:
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
    def get_carousel_images(self) -> list[CarouselImageItem]:
        """Get all carousel images."""
        images = self.repo.get_carousel_images()
        return [
            CarouselImageItem(
                id=img.id,
                image_url=img.image_url,
                alt_text=img.alt_text,
                display_order=img.display_order,
            )
            for img in images
        ]

    def update_carousel_images(self, images_data: list[dict]) -> list[CarouselImageItem]:
        """Update carousel images."""
        try:
            images = self.repo.update_carousel_images(images_data)
            self.repo.commit()
            return [
                CarouselImageItem(
                    id=img.id,
                    image_url=img.image_url,
                    alt_text=img.alt_text,
                    display_order=img.display_order,
                )
                for img in images
            ]
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update carousel images: {e!s}",
            ) from e
