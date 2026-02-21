from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.admin_repository import AdminRepository
from schemas.admin import (
    AdminEventResponse,
    AdminUserResponse,
    BannerMessageResponse,
    CreateEventRequest,
    EventRegistrationDetailResponse,
    UpdateBannerMessagesRequest,
    UpdateEventRequest,
)


class AdminService:
    """Service layer for admin-related business logic."""

    def __init__(self, db: Session):
        self.repo = AdminRepository(db)

    # ── User Operations ───────────────────────────────────────────────────

    def get_all_users(self) -> list[AdminUserResponse]:
        """Retrieve all users with their account details."""
        users = self.repo.get_all_users()
        return [
            AdminUserResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                handicap=user.handicap,
                email=user.account.email if user.account else None,
                role=user.account.role if user.account else None,
            )
            for user in users
        ]

    def update_user_role(self, user_id: int, role: str) -> AdminUserResponse:
        """Update a user's role."""
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        account = self.repo.get_user_account_by_user_id(user_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found",
            )

        try:
            self.repo.update_user_role(account, role)
            self.repo.commit()
            return AdminUserResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=user.phone_number,
                handicap=user.handicap,
                email=account.email,
                role=account.role,
            )
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user role: {e!s}",
            ) from e

    def delete_user(self, user_id: int) -> None:
        """Delete a user and their account."""
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        try:
            account = self.repo.get_user_account_by_user_id(user_id)
            if account:
                self.repo.delete_user_account(account)
            self.repo.delete_user(user)
            self.repo.commit()
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete user: {e!s}",
            ) from e

    # ── Event Operations ──────────────────────────────────────────────────

    def create_event(self, data: CreateEventRequest) -> AdminEventResponse:
        """Create a new event."""
        try:
            event = self.repo.create_event(
                township=data.township,
                state=data.state,
                zipcode=data.zipcode,
                golf_course=data.golf_course,
                date=data.date,
                start_time=data.start_time,
            )
            self.repo.commit()
            return AdminEventResponse.model_validate(event)
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create event: {e!s}",
            ) from e

    def update_event(self, event_id: int, data: UpdateEventRequest) -> AdminEventResponse:
        """Update an existing event."""
        event = self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        try:
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(event, field, value)
            self.repo.commit()
            return AdminEventResponse.model_validate(event)
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update event: {e!s}",
            ) from e

    def delete_event(self, event_id: int) -> None:
        """Delete an event."""
        event = self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        try:
            self.repo.delete_event(event)
            self.repo.commit()
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete event: {e!s}",
            ) from e

    def get_event_registrations(self, event_id: int) -> list[EventRegistrationDetailResponse]:
        """Get all registrations for a specific event."""
        event = self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        registrations = self.repo.get_event_registrations(event_id)
        return [EventRegistrationDetailResponse.model_validate(reg) for reg in registrations]

    # ── Banner Operations ─────────────────────────────────────────────────

    def update_banner_messages(
        self, data: UpdateBannerMessagesRequest
    ) -> list[BannerMessageResponse]:
        """Replace all banner messages with the provided list."""
        try:
            self.repo.delete_all_banners()
            new_banners = []
            for item in data.messages:
                banner = self.repo.create_banner(item.message)
                new_banners.append(banner)
            self.repo.commit()
            return [BannerMessageResponse.model_validate(b) for b in new_banners]
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update banner messages: {e!s}",
            ) from e
