import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AdminUser
from schemas.admin import (
    BannerResponse,
    CarouselImagesResponse,
    ContentResponse,
    CreateEventRequest,
    CreateExemptionCodeRequest,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    EventRegistrationsResponse,
    EventResponse,
    ExemptionCodeListResponse,
    ExemptionCodeResponse,
    MediaUploadResponse,
    PhotoAlbumCreate,
    PhotoAlbumListResponse,
    PhotoAlbumResponse,
    PhotoAlbumUpdate,
    UpdateBannerMessagesRequest,
    UpdateBannerSettingsRequest,
    UpdateCarouselImagesRequest,
    UpdateContentRequest,
    UpdateEventRequest,
    UpdateUserRoleRequest,
    UpdateUserRoleResponse,
    CreateEventPromoCodeRequest,
    EventPromoCodeListResponse,
    EventPromoCodeResponse,
)
from services.admin_service import AdminService
from schemas.partner import PartnerCreate, PartnerUpdate, PartnerResponse, PartnerListResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ===== Admin Users API =====
@router.get("/users")
def get_all_users(
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_all_users()


@router.post("/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: CreateUserRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> CreateUserResponse:
    """
    Create a new user account and send them a password setup email.
    Requires admin authentication.
    """
    service = AdminService(db)
    return service.create_user(data)


@router.put("/users/{user_id}/role", response_model=UpdateUserRoleResponse)
def update_user_role(
    user_id: int,
    data: UpdateUserRoleRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> UpdateUserRoleResponse:
    service = AdminService(db)
    updated_id, new_role = service.update_user_role(user_id, data.role)
    return UpdateUserRoleResponse(
        message="User role updated successfully", user_id=updated_id, new_role=new_role
    )


@router.delete("/users/{user_id}", response_model=DeleteUserResponse)
def delete_user(
    user_id: int, admin_user: AdminUser, db: Session = Depends(get_db)
) -> DeleteUserResponse:
    service = AdminService(db)
    service.delete_user(user_id)
    return DeleteUserResponse(message="User deleted successfully")


@router.put("/users/{user_id}/membership-exempt")
def toggle_membership_exempt(
    user_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    from models.user import User
    from services.auth_service import get_membership_expiration
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.membership_exempt = not user.membership_exempt
    if user.membership_exempt:
        # Grant membership through end of current year
        user.membership_expires_at = get_membership_expiration()
    db.commit()
    db.refresh(user)
    return {"message": "Membership exemption updated", "user_id": user_id, "membership_exempt": user.membership_exempt}


# ===== Admin Events API =====
@router.get("/events", response_model=List[EventResponse])
def get_all_events(
    order_by: str = Query(default="date"),
    order: str = Query(default="asc"),
    admin_user: AdminUser = None,
    db: Session = Depends(get_db),
) -> List[EventResponse]:
    service = AdminService(db)
    return service.get_all_events(sort_by=order_by, sort_order=order)


@router.get("/events/{event_id}/registrations", response_model=EventRegistrationsResponse)
def get_event_registrations(
    event_id: int, admin_user: AdminUser, db: Session = Depends(get_db)
) -> EventRegistrationsResponse:
    service = AdminService(db)
    registrations = service.get_event_registrations(event_id)
    return EventRegistrationsResponse(event_id=event_id, registrations=registrations)


@router.delete("/event-registrations/{registration_id}")
def delete_event_registration(
    registration_id: int, admin_user: AdminUser, db: Session = Depends(get_db)
):
    service = AdminService(db)
    success = service.delete_event_registration(registration_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")
    return {"message": "Registration deleted successfully", "registration_id": registration_id}


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: CreateEventRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> EventResponse:
    service = AdminService(db)
    event = service.create_event(data.model_dump())
    return EventResponse(**event)


@router.put("/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    data: UpdateEventRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> EventResponse:
    service = AdminService(db)
    event = service.update_event(event_id, data.model_dump(exclude_unset=True))
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse(**event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, admin_user: AdminUser, db: Session = Depends(get_db)) -> None:
    service = AdminService(db)
    service.delete_event(event_id)


# ===== Admin Banner API =====
@router.put("/banner-messages", response_model=BannerResponse)
def update_banner_messages(
    data: UpdateBannerMessagesRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> BannerResponse:
    service = AdminService(db)
    service.update_banner_messages(data.messages)
    return BannerResponse(message="Banner messages updated successfully")


@router.put("/banner-settings", response_model=BannerResponse)
def update_banner_settings(
    data: UpdateBannerSettingsRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> BannerResponse:
    return BannerResponse(
        message="Banner settings updated successfully", data={"display_count": data.display_count}
    )


# ===== Admin Photos API =====
@router.get("/photo-albums", response_model=PhotoAlbumListResponse)
def get_all_albums(
    admin_user: AdminUser, db: Session = Depends(get_db)
) -> PhotoAlbumListResponse:
    service = AdminService(db)
    albums = service.get_all_photo_albums()
    return PhotoAlbumListResponse(albums=[PhotoAlbumResponse.model_validate(a) for a in albums])


@router.post("/photo-albums", response_model=PhotoAlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(
    data: PhotoAlbumCreate, admin_user: AdminUser, db: Session = Depends(get_db)
) -> PhotoAlbumResponse:
    service = AdminService(db)
    album = service.create_photo_album(data.model_dump())
    return PhotoAlbumResponse.model_validate(album)


@router.put("/photo-albums/{album_id}", response_model=PhotoAlbumResponse)
def update_album(
    album_id: int,
    data: PhotoAlbumUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> PhotoAlbumResponse:
    service = AdminService(db)
    album = service.update_photo_album(album_id, data.model_dump(exclude_none=True))
    return PhotoAlbumResponse.model_validate(album)


@router.delete("/photo-albums/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, admin_user: AdminUser, db: Session = Depends(get_db)) -> None:
    service = AdminService(db)
    service.delete_photo_album(album_id)


# ===== Admin Content API =====
@router.get("/content", response_model=ContentResponse)
def get_site_content(admin_user: AdminUser, db: Session = Depends(get_db)) -> ContentResponse:
    service = AdminService(db)
    content = service.get_all_content()
    return ContentResponse(content=content)


@router.put("/content", response_model=BannerResponse)
def update_content(
    data: UpdateContentRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> BannerResponse:
    service = AdminService(db)
    service.update_content(data.content)
    return BannerResponse(message="Content updated successfully")


# ===== Admin Media API =====
@router.post("/media/upload", response_model=MediaUploadResponse)
async def upload_image(
    admin_user: AdminUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image files are allowed")
    file_ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        return MediaUploadResponse(message="Image uploaded successfully", url=f"/uploads/{unique_filename}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload image: {e!s}") from e


@router.get("/media/carousel", response_model=CarouselImagesResponse)
def get_carousel_images(
    admin_user: AdminUser, db: Session = Depends(get_db)
) -> CarouselImagesResponse:
    service = AdminService(db)
    images = service.get_carousel_images()
    return CarouselImagesResponse(images=images)


@router.put("/media/carousel", response_model=CarouselImagesResponse)
def update_carousel_images(
    data: UpdateCarouselImagesRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> CarouselImagesResponse:
    service = AdminService(db)
    images = service.update_carousel_images(data.images)
    return CarouselImagesResponse(images=images)


# ===== Partners API =====
@router.get("/partners", response_model=PartnerListResponse)
def get_all_partners(admin_user: AdminUser, db: Session = Depends(get_db)):
    service = AdminService(db)
    partners = service.get_all_partners()
    return PartnerListResponse(partners=partners)


@router.post("/partners", response_model=PartnerResponse)
def create_partner(data: PartnerCreate, admin_user: AdminUser, db: Session = Depends(get_db)):
    service = AdminService(db)
    return service.create_partner(
        name=data.name, logo_url=data.logo_url,
        website_url=data.website_url, display_order=data.display_order
    )


@router.put("/partners/{partner_id}", response_model=PartnerResponse)
def update_partner(partner_id: int, data: PartnerUpdate, admin_user: AdminUser, db: Session = Depends(get_db)):
    service = AdminService(db)
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    return service.update_partner(partner_id, **update_data)


@router.delete("/partners/{partner_id}")
def delete_partner(partner_id: int, admin_user: AdminUser, db: Session = Depends(get_db)):
    service = AdminService(db)
    service.delete_partner(partner_id)
    return {"message": "Partner deleted successfully"}


# ===== Exemption Codes API =====
@router.get("/exemption-codes", response_model=ExemptionCodeListResponse)
def get_exemption_codes(admin_user: AdminUser, db: Session = Depends(get_db)):
    from models.exemption_code import ExemptionCode
    codes = db.query(ExemptionCode).order_by(ExemptionCode.created_at.desc()).all()
    return ExemptionCodeListResponse(codes=codes)


@router.post("/exemption-codes", response_model=ExemptionCodeResponse, status_code=status.HTTP_201_CREATED)
def create_exemption_code(
    data: CreateExemptionCodeRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    import secrets
    from models.exemption_code import ExemptionCode

    code_str = data.code or secrets.token_urlsafe(8).upper()[:8]

    existing = db.query(ExemptionCode).filter(ExemptionCode.code == code_str).first()
    if existing:
        raise HTTPException(status_code=400, detail="Code already exists")

    code = ExemptionCode(
        code=code_str,
        max_uses=data.max_uses,
        expires_at=data.expires_at,
    )
    db.add(code)
    db.commit()
    db.refresh(code)
    return code


@router.delete("/exemption-codes/{code_id}")
def delete_exemption_code(code_id: int, admin_user: AdminUser, db: Session = Depends(get_db)):
    from models.exemption_code import ExemptionCode
    code = db.query(ExemptionCode).filter(ExemptionCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    db.delete(code)
    db.commit()
    return {"message": "Exemption code deleted"}


# ===== Event Promo Codes API =====
@router.get("/event-promo-codes", response_model=EventPromoCodeListResponse)
def get_event_promo_codes(admin_user: AdminUser, db: Session = Depends(get_db)):
    from models.event_promo_code import EventPromoCode
    codes = db.query(EventPromoCode).order_by(EventPromoCode.created_at.desc()).all()
    result = []
    for c in codes:
        result.append(EventPromoCodeResponse(
            id=c.id,
            code=c.code,
            discount_type=c.discount_type,
            discount_value=float(c.discount_value) if c.discount_value else None,
            event_id=c.event_id,
            event_name=c.event.golf_course if c.event else None,
            max_uses=c.max_uses,
            times_used=c.times_used,
            is_active=c.is_active,
            created_at=c.created_at,
            expires_at=c.expires_at,
        ))
    return EventPromoCodeListResponse(codes=result)


@router.post("/event-promo-codes", response_model=EventPromoCodeResponse, status_code=status.HTTP_201_CREATED)
def create_event_promo_code(
    data: CreateEventPromoCodeRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    import secrets
    from models.event_promo_code import EventPromoCode
    from models.event import Event

    if data.discount_type not in ("member_price", "free", "percent"):
        raise HTTPException(status_code=400, detail="discount_type must be 'member_price', 'free', or 'percent'")
    if data.discount_type == "percent":
        if not data.discount_value or data.discount_value <= 0 or data.discount_value > 100:
            raise HTTPException(status_code=400, detail="discount_value must be between 1 and 100 for percent type")
    if data.event_id:
        event = db.query(Event).filter(Event.id == data.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    code_str = data.code or secrets.token_urlsafe(8).upper()[:8]
    existing = db.query(EventPromoCode).filter(EventPromoCode.code == code_str).first()
    if existing:
        raise HTTPException(status_code=400, detail="Code already exists")

    promo = EventPromoCode(
        code=code_str,
        discount_type=data.discount_type,
        discount_value=data.discount_value if data.discount_type == "percent" else None,
        event_id=data.event_id,
        max_uses=data.max_uses,
        expires_at=data.expires_at,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)

    return EventPromoCodeResponse(
        id=promo.id,
        code=promo.code,
        discount_type=promo.discount_type,
        discount_value=float(promo.discount_value) if promo.discount_value else None,
        event_id=promo.event_id,
        event_name=promo.event.golf_course if promo.event else None,
        max_uses=promo.max_uses,
        times_used=promo.times_used,
        is_active=promo.is_active,
        created_at=promo.created_at,
        expires_at=promo.expires_at,
    )


@router.delete("/event-promo-codes/{code_id}")
def delete_event_promo_code(code_id: int, admin_user: AdminUser, db: Session = Depends(get_db)):
    from models.event_promo_code import EventPromoCode
    code = db.query(EventPromoCode).filter(EventPromoCode.id == code_id).first()
    if not code:
        raise HTTPException(status_code=404, detail="Promo code not found")
    db.delete(code)
    db.commit()
    return {"message": "Promo code deleted"}