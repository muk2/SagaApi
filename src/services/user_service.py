from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.user_repository import UserRepository
from schemas.user import (
    EventRegistrationResponse,
    PasswordResetRequest,
    UserProfileUpdateRequest,
)
from services.auth_service import hash_password, verify_password


class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_user_events(self, user_id: int) -> list[EventRegistrationResponse]:
        """Get all events a user is registered for."""
        registrations = self.repo.get_user_registered_events(user_id)

        return [
            EventRegistrationResponse(
                id=reg.id,
                event_id=reg.event_id,
                township=reg.event.township,
                golf_course=reg.event.golf_course,
                registered_at=reg.registered_at,
                status=reg.status,
            )
            for reg in registrations
        ]

    def update_user_profile(
        self, user_id: int, data: UserProfileUpdateRequest
    ) -> tuple[str, int | None]:
        """Update user profile (currently only handicap)."""
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        try:
            updated_user = self.repo.update_user_handicap(user_id, data.handicap)
            self.repo.commit()
            return "Profile updated successfully", updated_user.handicap if updated_user else None
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update profile: {e!s}",
            ) from e

    def reset_password(self, user_id: int, data: PasswordResetRequest) -> str:
        """Reset user password after verifying current password."""
        account = self.repo.get_user_account_by_user_id(user_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User account not found"
            )

        # Verify current password
        if not verify_password(data.current_password, account.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        # Validate new password is different
        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        try:
            new_hash = hash_password(data.new_password)
            self.repo.update_user_password(user_id, new_hash)
            self.repo.commit()
            return "Password reset successfully"
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reset password: {e!s}",
            ) from e

    def register_for_event(self, user_id: int, event_id: int) -> EventRegistrationResponse:
        """Register a user for an event."""
        # Verify user exists
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Verify event exists
        event = self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )

        try:
            registration = self.repo.create_event_registration(user_id, event_id)
            if not registration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already registered for this event",
                )

            self.repo.commit()

            return EventRegistrationResponse(
                id=registration.id,
                event_id=registration.event_id,
                township=event.township,
                golf_course=event.golf_course,
                registered_at=registration.registered_at,
                status=registration.status,
            )
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register for event: {e!s}",
            ) from e
