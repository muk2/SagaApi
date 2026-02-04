from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Tuple, Optional, List
from repositories.user_repository import UserRepository
from schemas.user import (
    EventRegistrationResponse,
    PasswordResetRequest,
    UserProfileUpdateRequest,
)
from services.auth_service import hash_password, verify_password
from sqlalchemy.exc import IntegrityError

class UserService:
    """Service layer for user-related business logic."""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_user_events(self, user_id: int) -> List[EventRegistrationResponse]:
        """Get all events a user is registered for."""

        user_account = self.repo.get_user_account_by_user_id(user_id)

        if not user_account:
            return []
        
        registrations = self.repo.get_user_registered_events(user_account.id)

        return [
            EventRegistrationResponse(
                id=reg.id,
                event_id=reg.event_id,
                township=reg.event.township,
                state=reg.event.state,
                golf_course=reg.event.golf_course,
                date=reg.event.date,
                start_time = reg.event.start_time,
            )
            for reg in registrations
        ]


    def update_user_profile(
        self, user_id: int, data: UserProfileUpdateRequest
    ) -> Tuple[str, Optional[int]]:
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
        except IntegrityError as e:
            self.repo.rollback()
            # Check if it's the check constraint violation
            if "check_valid_chars" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not a valid handicap"
                ) from e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update profile: {e!s}",
            ) from e
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

    def register_for_event(
        self, 
        user_account_id: int, 
        event_id: int,
        email: str,
        phone: str,
        handicap: Optional[str] = None
    ) -> EventRegistrationResponse:
        """Register a user for an event."""
        # Verify event exists
        event = self.repo.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )

        try:
            registration = self.repo.create_event_registration(
                user_id=user_account_id,  
                event_id=event_id,
                email=email,
                phone=phone,
                handicap=handicap
            )
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