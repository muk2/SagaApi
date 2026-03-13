import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import CurrentUser
from schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SignUpRequest,
    SignUpResponse,
    UserResponse,
)
from services.auth_service import AuthService
from services.email_service import EmailService
from services.north_payment_service import charge_card, NorthDeclinedError, NorthGatewayError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignUpResponse)
async def signup(data: SignUpRequest, db: Session = Depends(get_db)) -> SignUpResponse:
    """
    Register a new user.

    Creates both a User record (profile data) and a UserAccount record (credentials).
    If a payment_token is provided, charges the membership fee before finalizing.
    Returns the created user information without sensitive data.
    """
    service = AuthService(db)
    user, _ = service.signup(data)

    # Process membership payment if token provided
    if data.payment_token:
        try:
            # Look up the membership price from the database
            from models.membership_option import MembershipOption
            membership_option = db.query(MembershipOption).filter(
                MembershipOption.name == data.membership,
                MembershipOption.is_active == True,
            ).first()

            if not membership_option:
                service.repo.delete_user(user.id)
                service.repo.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Membership type '{data.membership}' not found",
                )

            amount = float(membership_option.price)
            result = await charge_card(data.payment_token, amount)

            if not result.approved:
                # Rollback user creation on payment failure
                service.repo.delete_user(user.id)
                service.repo.commit()
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Payment was declined. Please try a different card.",
                )

            logger.info(
                "Membership payment approved for user %s: transaction_id=%s amount=%s",
                user.id, result.transaction_id, amount,
            )

        except NorthDeclinedError as e:
            # Rollback user creation on decline
            service.repo.delete_user(user.id)
            service.repo.commit()
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(e) or "Payment was declined. Please try a different card.",
            )
        except NorthGatewayError as e:
            # Rollback user creation on gateway error
            service.repo.delete_user(user.id)
            service.repo.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e) or "Payment processing failed. Please try again.",
            )

        # Send membership confirmation email (after successful payment)
        try:
            EmailService().send_membership_confirmation_email(
                to_email=data.email,
                member_name=f"{user.first_name} {user.last_name}",
                membership_type=user.membership,
                price=amount,
            )
        except Exception:
            logger.exception("Failed to send membership email for user_id=%s", user.id)

    user_response = UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        role="user",
        email=data.email,
        phone_number=user.phone_number,
        handicap=user.handicap,
        membership=user.membership
    )

    return SignUpResponse(message="User created successfully", user=user_response)


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    Validates credentials against stored password hash.
    Returns a JWT access token for subsequent authenticated requests.
    """
    service = AuthService(db)
    token, user_response = service.login(data)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: CurrentUser, db: Session = Depends(get_db)) -> LogoutResponse:
    """
    Logout the current user by invalidating their token.

    Increments the user's token_version, which invalidates all existing tokens.
    Requires a valid JWT token in the Authorization header.
    """
    service = AuthService(db)
    service.logout(current_user.id)
    return LogoutResponse(message="Successfully logged out")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)) -> ForgotPasswordResponse:
    """
    Initiate password reset flow.

    Generates a reset token and stores it in the database.
    In production, this token should be sent to the user's email.

    Returns success regardless of whether email exists (prevents email enumeration).
    """
    service = AuthService(db)
    service.forgot_password(data)
    return ForgotPasswordResponse(message="Password reset email sent")


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)) -> ResetPasswordResponse:
    """
    Reset user password using a valid reset token.

    Validates the token, checks expiration, updates the password,
    and invalidates all existing JWT tokens for security.
    """
    service = AuthService(db)
    service.reset_password(data)
    return ResetPasswordResponse(message="Password reset successful")
