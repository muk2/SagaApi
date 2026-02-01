import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AdminUser
from schemas.admin import (
    BannerResponse,
    CarouselImagesResponse,
    ContentResponse,
    CreateEventRequest,
    DeleteUserResponse,
    EventRegistrationsResponse,
    EventResponse,
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
    UserListResponse,
)
from services.admin_service import AdminService

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ===== Admin Users API =====
@router.get("/users", response_model=UserListResponse)
def get_all_users(admin_user: AdminUser, db: Session = Depends(get_db)) -> UserListResponse:
    """
    Get all users.
    Requires admin authentication.
    """
    service = AdminService(db)
    users = service.get_all_users()
    return UserListResponse(users=users)


@router.put("/users/{user_id}/role", response_model=UpdateUserRoleResponse)
def update_user_role(
    user_id: int,
    data: UpdateUserRoleRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> UpdateUserRoleResponse:
    """
    Update user role.
    Requires admin authentication.
    """
    service = AdminService(db)
    updated_id, new_role = service.update_user_role(user_id, data.role)
    return UpdateUserRoleResponse(
        message="User role updated successfully", user_id=updated_id, new_role=new_role
    )


@router.delete("/users/{user_id}", response_model=DeleteUserResponse)
def delete_user(
    user_id: int, admin_user: AdminUser, db: Session = Depends(get_db)
) -> DeleteUserResponse:
    """
    Delete user.
    Requires admin authentication.
    """
    service = AdminService(db)
    service.delete_user(user_id)
    return DeleteUserResponse(message="User deleted successfully")


@router.get("/events/{event_id}/registrations", response_model=EventRegistrationsResponse)
def get_event_registrations(
    event_id: int, admin_user: AdminUser, db: Session = Depends(get_db)
) -> EventRegistrationsResponse:
    """
    Get event registrations.
    Requires admin authentication.
    """
    service = AdminService(db)
    registrations = service.get_event_registrations(event_id)
    return EventRegistrationsResponse(event_id=event_id, registrations=registrations)


# ===== Admin Events API =====
@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: CreateEventRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> EventResponse:
    """
    Create event.
    Requires admin authentication.
    """
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
    """
    Update event.
    Requires admin authentication.
    """
    service = AdminService(db)
    event = service.update_event(event_id, data.model_dump(exclude_none=True))
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse(**event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, admin_user: AdminUser, db: Session = Depends(get_db)) -> None:
    """
    Delete event.
    Requires admin authentication.
    """
    service = AdminService(db)
    service.delete_event(event_id)


# ===== Admin Banner API =====
@router.put("/banner-messages", response_model=BannerResponse)
def update_banner_messages(
    data: UpdateBannerMessagesRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> BannerResponse:
    """
    Update messages array.
    Requires admin authentication.
    """
    service = AdminService(db)
    service.update_banner_messages(data.messages)
    return BannerResponse(message="Banner messages updated successfully")


@router.put("/banner-settings", response_model=BannerResponse)
def update_banner_settings(
    data: UpdateBannerSettingsRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> BannerResponse:
    """
    Update display count.
    Requires admin authentication.
    Note: This endpoint updates a banner-related setting.
    Implementation depends on how display_count is stored (e.g., in a settings table).
    """
    # This is a placeholder - actual implementation depends on where display_count is stored
    return BannerResponse(
        message="Banner settings updated successfully", data={"display_count": data.display_count}
    )


# ===== Admin Photos API =====
@router.get("/photo-albums", response_model=PhotoAlbumListResponse)
def get_all_albums(
    admin_user: AdminUser, db: Session = Depends(get_db)
) -> PhotoAlbumListResponse:
    """
    Get all albums.
    Requires admin authentication.
    """
    service = AdminService(db)
    albums = service.get_all_photo_albums()
    return PhotoAlbumListResponse(albums=albums)


@router.post("/photo-albums", response_model=PhotoAlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(
    data: PhotoAlbumCreate, admin_user: AdminUser, db: Session = Depends(get_db)
) -> PhotoAlbumResponse:
    """
    Create album.
    Requires admin authentication.
    """
    service = AdminService(db)
    album = service.create_photo_album(data.model_dump())
    return album


@router.put("/photo-albums/{album_id}", response_model=PhotoAlbumResponse)
def update_album(
    album_id: int,
    data: PhotoAlbumUpdate,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> PhotoAlbumResponse:
    """
    Update album.
    Requires admin authentication.
    """
    service = AdminService(db)
    album = service.update_photo_album(album_id, data.model_dump(exclude_none=True))
    return album


@router.delete("/photo-albums/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(album_id: int, admin_user: AdminUser, db: Session = Depends(get_db)) -> None:
    """
    Delete album.
    Requires admin authentication.
    """
    service = AdminService(db)
    service.delete_photo_album(album_id)


# ===== Admin Content API =====
@router.get("/content", response_model=ContentResponse)
def get_site_content(admin_user: AdminUser, db: Session = Depends(get_db)) -> ContentResponse:
    """
    Get site content.
    Requires admin authentication.
    """
    service = AdminService(db)
    content = service.get_all_content()
    return ContentResponse(content=content)


@router.put("/content", response_model=BannerResponse)
def update_content(
    data: UpdateContentRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> BannerResponse:
    """
    Update content.
    Requires admin authentication.
    """
    service = AdminService(db)
    service.update_content(data.content)
    return BannerResponse(message="Content updated successfully")


# ===== Admin Media API =====
@router.post("/media/upload", response_model=MediaUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    admin_user: AdminUser = Depends(),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    """
    Upload image (multipart/form-data).
    Requires admin authentication.

    Note: This is a basic implementation. In production, you should:
    - Use cloud storage (S3, GCS, etc.)
    - Validate file type and size
    - Generate thumbnails
    - Add virus scanning
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed",
        )

    # Generate unique filename
    file_ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"

    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # In production, this would be a CDN URL or S3 URL
        file_url = f"/uploads/{unique_filename}"

        return MediaUploadResponse(message="Image uploaded successfully", url=file_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {e!s}",
        ) from e


@router.get("/media/carousel", response_model=CarouselImagesResponse)
def get_carousel_images(
    admin_user: AdminUser, db: Session = Depends(get_db)
) -> CarouselImagesResponse:
    """
    Get carousel images.
    Requires admin authentication.
    """
    service = AdminService(db)
    images = service.get_carousel_images()
    return CarouselImagesResponse(images=images)


@router.put("/media/carousel", response_model=CarouselImagesResponse)
def update_carousel_images(
    data: UpdateCarouselImagesRequest, admin_user: AdminUser, db: Session = Depends(get_db)
) -> CarouselImagesResponse:
    """
    Update carousel images.
    Requires admin authentication.
    """
    service = AdminService(db)
    images = service.update_carousel_images(data.images)
    return CarouselImagesResponse(images=images)
