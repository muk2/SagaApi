from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import AdminUser
from schemas.admin import (
    AdminUserListResponse,
    CreateEventRequest,
    CreateEventResponse,
    DeleteEventResponse,
    DeleteUserResponse,
    EventRegistrationsListResponse,
    UpdateBannerMessagesRequest,
    UpdateBannerMessagesResponse,
    UpdateEventRequest,
    UpdateEventResponse,
    UpdateUserRoleRequest,
    UpdateUserRoleResponse,
)
from services.admin_service import AdminService

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Admin Users API ───────────────────────────────────────────────────────────


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    """
    List all users with their account details.
    Requires admin role.
    """
    service = AdminService(db)
    users = service.get_all_users()
    return AdminUserListResponse(users=users)


@router.put("/users/{user_id}/role", response_model=UpdateUserRoleResponse)
def update_user_role(
    user_id: int,
    data: UpdateUserRoleRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> UpdateUserRoleResponse:
    """
    Update a user's role.
    Requires admin role.
    """
    service = AdminService(db)
    user = service.update_user_role(user_id, data.role)
    return UpdateUserRoleResponse(message="User role updated successfully", user=user)


@router.delete("/users/{user_id}", response_model=DeleteUserResponse)
def delete_user(
    user_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> DeleteUserResponse:
    """
    Delete a user and their account.
    Requires admin role.
    """
    service = AdminService(db)
    service.delete_user(user_id)
    return DeleteUserResponse(message="User deleted successfully")


# ── Admin Events API ──────────────────────────────────────────────────────────


@router.post("/events", response_model=CreateEventResponse)
def create_event(
    data: CreateEventRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> CreateEventResponse:
    """
    Create a new event.
    Requires admin role.
    """
    service = AdminService(db)
    event = service.create_event(data)
    return CreateEventResponse(message="Event created successfully", event=event)


@router.put("/events/{event_id}", response_model=UpdateEventResponse)
def update_event(
    event_id: int,
    data: UpdateEventRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> UpdateEventResponse:
    """
    Update an existing event.
    Requires admin role.
    """
    service = AdminService(db)
    event = service.update_event(event_id, data)
    return UpdateEventResponse(message="Event updated successfully", event=event)


@router.delete("/events/{event_id}", response_model=DeleteEventResponse)
def delete_event(
    event_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> DeleteEventResponse:
    """
    Delete an event.
    Requires admin role.
    """
    service = AdminService(db)
    service.delete_event(event_id)
    return DeleteEventResponse(message="Event deleted successfully")


@router.get(
    "/events/{event_id}/registrations",
    response_model=EventRegistrationsListResponse,
)
def get_event_registrations(
    event_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> EventRegistrationsListResponse:
    """
    Get all registrations for a specific event.
    Requires admin role.
    """
    service = AdminService(db)
    registrations = service.get_event_registrations(event_id)
    return EventRegistrationsListResponse(event_id=event_id, registrations=registrations)


# ── Admin Banner API ──────────────────────────────────────────────────────────


@router.put("/banner-messages", response_model=UpdateBannerMessagesResponse)
def update_banner_messages(
    data: UpdateBannerMessagesRequest,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
) -> UpdateBannerMessagesResponse:
    """
    Replace all banner messages with the provided list.
    Requires admin role.
    """
    service = AdminService(db)
    banners = service.update_banner_messages(data)
    return UpdateBannerMessagesResponse(
        message="Banner messages updated successfully", banners=banners
    )
