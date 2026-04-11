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
    If a paypal_order_id is provided, captures the PayPal order before finalizing.
    If an exemption_code is provided, validates it and marks user as exempt.
    Returns the created user information without sensitive data.
    """
    # Validate exemption code if provided
    is_exempt = False
    if data.exemption_code:
        from models.exemption_code import ExemptionCode
        from datetime import datetime, timezone as tz

        code = db.query(ExemptionCode).filter(
            ExemptionCode.code == data.exemption_code.strip(),
            ExemptionCode.is_active == True,
        ).first()

        if not code:
            raise HTTPException(status_code=400, detail="Invalid exemption code")
        if code.expires_at and datetime.now(tz.utc) > code.expires_at:
            raise HTTPException(status_code=400, detail="This exemption code has expired")
        if code.times_used >= code.max_uses:
            raise HTTPException(status_code=400, detail="This exemption code has reached its usage limit")

        is_exempt = True

    service = AuthService(db)
    user, _ = service.signup(data, membership_exempt=is_exempt)

    # Increment exemption code usage after successful signup
    if is_exempt and data.exemption_code:
        from models.exemption_code import ExemptionCode
        code = db.query(ExemptionCode).filter(
            ExemptionCode.code == data.exemption_code.strip(),
        ).first()
        if code:
            code.times_used += 1
            db.commit()

    # Process membership payment via North if payment token provided (skip if exempt)
    amount = 0.0
    if data.payment_token and not is_exempt:
        try:
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
            charge = await charge_card(data.payment_token, amount)

            logger.info(
                "Membership payment charged for user %s: transaction_id=%s amount=%s",
                user.id, charge.transaction_id, amount,
            )

        except NorthDeclinedError as e:
            service.repo.delete_user(user.id)
            service.repo.commit()
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(e) or "Payment was declined. Please try again.",
            )
        except NorthGatewayError as e:
            service.repo.delete_user(user.id)
            service.repo.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(e) or "Payment processing failed. Please try again.",
            )

    # Send membership confirmation email (for both paid and free signups)
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
        ghin_number=user.ghin_number,
        membership=user.membership,
        membership_expired=False,
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


@router.post("/validate-exemption-code")
def validate_exemption_code(data: dict, db: Session = Depends(get_db)):
    """Validate an exemption code for signup. Public endpoint."""
    from models.exemption_code import ExemptionCode
    from datetime import datetime, timezone as tz

    code_str = data.get("code", "").strip()
    if not code_str:
        raise HTTPException(status_code=400, detail="Code is required")

    code = db.query(ExemptionCode).filter(
        ExemptionCode.code == code_str,
        ExemptionCode.is_active == True,
    ).first()

    if not code:
        raise HTTPException(status_code=404, detail="Invalid exemption code")

    if code.expires_at and datetime.now(tz.utc) > code.expires_at:
        raise HTTPException(status_code=400, detail="This code has expired")

    if code.times_used >= code.max_uses:
        raise HTTPException(status_code=400, detail="This code has reached its usage limit")

    return {"valid": True, "message": "Code is valid"}


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
