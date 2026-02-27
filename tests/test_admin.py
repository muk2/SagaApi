"""Comprehensive tests for admin dashboard API endpoints."""

from datetime import date, time
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.models.banner_message import Banner
from src.models.event import Event
from src.models.event_registration import EventRegistration
from src.models.user import User, UserAccount

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_user_account(user_id=1, email="admin@test.com", role="admin"):
    account = MagicMock(spec=UserAccount)
    account.id = 1
    account.user_id = user_id
    account.email = email
    account.role = role
    account.password_hash = "hashed"
    account.token_version = 1
    return account


def _make_user(user_id=1, role="admin", email="admin@test.com"):
    user = MagicMock(spec=User)
    user.id = user_id
    user.first_name = "Admin"
    user.last_name = "User"
    user.phone_number = "1234567890"
    user.handicap = "5"
    user.user_account_id = 1
    user.account = _make_user_account(user_id=user_id, email=email, role=role)
    return user


def _make_non_admin_user(user_id=2):
    user = _make_user(user_id=user_id, role="user", email="user@test.com")
    user.first_name = "Regular"
    user.last_name = "Member"
    return user


def _make_event(event_id=1):
    event = MagicMock(spec=Event)
    event.id = event_id
    event.township = "Springfield"
    event.state = "IL"
    event.zipcode = "62701"
    event.golf_course = "Lincoln Greens"
    event.date = date(2026, 6, 15)
    event.start_time = time(8, 0)
    return event


def _make_registration(reg_id=1, event_id=1, user_id=1):
    reg = MagicMock(spec=EventRegistration)
    reg.id = reg_id
    reg.event_id = event_id
    reg.user_id = user_id
    reg.guest_id = None
    reg.handicap = "10"
    reg.email = "player@test.com"
    reg.phone = "5551234567"
    reg.payment_status = "pending"
    reg.payment_method = None
    reg.amount_paid = None
    reg.price_tier_id = None
    return reg


def _make_banner(banner_id=1, message="Welcome!"):
    banner = MagicMock(spec=Banner)
    banner.id = banner_id
    banner.message = message
    return banner


@pytest.fixture
def admin_user():
    return _make_user()


@pytest.fixture
def non_admin_user():
    return _make_non_admin_user()


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(admin_user):
    """Create a test client with overridden dependencies."""
    from src.core.database import get_db
    from src.core.dependencies import get_current_user
    from main import app

    def override_get_db():
        return MagicMock()

    def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def non_admin_client(non_admin_user):
    """Create a test client with a non-admin user."""
    from src.core.database import get_db
    from src.core.dependencies import get_current_user
    from main import app

    def override_get_db():
        return MagicMock()

    def override_get_current_user():
        return non_admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    """Create a test client with no authentication."""
    from main import app

    app.dependency_overrides.clear()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ── Authorization Tests ───────────────────────────────────────────────────────


class TestAdminAuthorization:
    """Test that admin endpoints enforce admin role."""

    def test_non_admin_cannot_list_users(self, non_admin_client):
        response = non_admin_client.get("/api/admin/users")
        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"

    def test_non_admin_cannot_update_role(self, non_admin_client):
        response = non_admin_client.put("/api/admin/users/1/role", json={"role": "admin"})
        assert response.status_code == 403

    def test_non_admin_cannot_delete_user(self, non_admin_client):
        response = non_admin_client.delete("/api/admin/users/1")
        assert response.status_code == 403

    def test_non_admin_cannot_create_event(self, non_admin_client):
        response = non_admin_client.post(
            "/api/admin/events",
            json={
                "township": "Test",
                "state": "IL",
                "zipcode": "62701",
                "golf_course": "Test Course",
                "date": "2026-06-15",
                "start_time": "08:00:00",
            },
        )
        assert response.status_code == 403

    def test_non_admin_cannot_update_event(self, non_admin_client):
        response = non_admin_client.put("/api/admin/events/1", json={"township": "New Town"})
        assert response.status_code == 403

    def test_non_admin_cannot_delete_event(self, non_admin_client):
        response = non_admin_client.delete("/api/admin/events/1")
        assert response.status_code == 403

    def test_non_admin_cannot_get_registrations(self, non_admin_client):
        response = non_admin_client.get("/api/admin/events/1/registrations")
        assert response.status_code == 403

    def test_non_admin_cannot_update_banners(self, non_admin_client):
        response = non_admin_client.put("/api/admin/banner-messages", json={"messages": []})
        assert response.status_code == 403

    def test_unauthenticated_cannot_list_users(self, unauthenticated_client):
        response = unauthenticated_client.get("/api/admin/users")
        assert response.status_code == 401


# ── Admin Users Tests ─────────────────────────────────────────────────────────


class TestAdminUsers:
    """Test admin user management endpoints."""

    @patch("src.routers.admin.AdminService")
    def test_list_users_success(self, mock_service_cls, client):
        from schemas.admin import AdminUserResponse

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.get_all_users.return_value = [
            AdminUserResponse(
                id=1,
                first_name="Admin",
                last_name="User",
                phone_number="1234567890",
                handicap="5",
                email="admin@test.com",
                role="admin",
            ),
            AdminUserResponse(
                id=2,
                first_name="Regular",
                last_name="Member",
                phone_number=None,
                handicap=None,
                email="user@test.com",
                role="user",
            ),
        ]

        response = client.get("/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["users"][0]["email"] == "admin@test.com"
        assert data["users"][0]["role"] == "admin"
        assert data["users"][1]["role"] == "user"

    @patch("src.routers.admin.AdminService")
    def test_list_users_empty(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.get_all_users.return_value = []

        response = client.get("/api/admin/users")
        assert response.status_code == 200
        assert response.json()["users"] == []

    @patch("src.routers.admin.AdminService")
    def test_update_user_role_success(self, mock_service_cls, client):
        from schemas.admin import AdminUserResponse

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.update_user_role.return_value = AdminUserResponse(
            id=2,
            first_name="Regular",
            last_name="Member",
            phone_number=None,
            handicap=None,
            email="user@test.com",
            role="admin",
        )

        response = client.put("/api/admin/users/2/role", json={"role": "admin"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User role updated successfully"
        assert data["user"]["role"] == "admin"
        mock_service.update_user_role.assert_called_once_with(2, "admin")

    @patch("src.routers.admin.AdminService")
    def test_update_user_role_not_found(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.update_user_role.side_effect = HTTPException(
            status_code=404, detail="User not found"
        )

        response = client.put("/api/admin/users/999/role", json={"role": "admin"})
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    @patch("src.routers.admin.AdminService")
    def test_update_user_role_missing_body(self, mock_service_cls, client):
        response = client.put("/api/admin/users/1/role")
        assert response.status_code == 422

    @patch("src.routers.admin.AdminService")
    def test_delete_user_success(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.delete_user.return_value = None

        response = client.delete("/api/admin/users/2")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User deleted successfully"
        mock_service.delete_user.assert_called_once_with(2)

    @patch("src.routers.admin.AdminService")
    def test_delete_user_not_found(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.delete_user.side_effect = HTTPException(
            status_code=404, detail="User not found"
        )

        response = client.delete("/api/admin/users/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"


# ── Admin Events Tests ────────────────────────────────────────────────────────


class TestAdminEvents:
    """Test admin event management endpoints."""

    @patch("src.routers.admin.AdminService")
    def test_create_event_success(self, mock_service_cls, client):
        from schemas.admin import AdminEventResponse

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.create_event.return_value = AdminEventResponse(
            id=1,
            township="Springfield",
            state="IL",
            zipcode="62701",
            golf_course="Lincoln Greens",
            date=date(2026, 6, 15),
            start_time=time(8, 0),
        )

        payload = {
            "township": "Springfield",
            "state": "IL",
            "zipcode": "62701",
            "golf_course": "Lincoln Greens",
            "date": "2026-06-15",
            "start_time": "08:00:00",
        }
        response = client.post("/api/admin/events", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Event created successfully"
        assert data["event"]["golf_course"] == "Lincoln Greens"
        assert data["event"]["township"] == "Springfield"

    @patch("src.routers.admin.AdminService")
    def test_create_event_validation_error(self, mock_service_cls, client):
        # Missing required fields
        response = client.post("/api/admin/events", json={"township": "Test"})
        assert response.status_code == 422

    @patch("src.routers.admin.AdminService")
    def test_update_event_success(self, mock_service_cls, client):
        from schemas.admin import AdminEventResponse

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.update_event.return_value = AdminEventResponse(
            id=1,
            township="New Town",
            state="IL",
            zipcode="62701",
            golf_course="Lincoln Greens",
            date=date(2026, 6, 15),
            start_time=time(8, 0),
        )

        response = client.put("/api/admin/events/1", json={"township": "New Town"})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Event updated successfully"
        assert data["event"]["township"] == "New Town"
        mock_service.update_event.assert_called_once()

    @patch("src.routers.admin.AdminService")
    def test_update_event_not_found(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.update_event.side_effect = HTTPException(
            status_code=404, detail="Event not found"
        )

        response = client.put("/api/admin/events/999", json={"township": "New Town"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Event not found"

    @patch("src.routers.admin.AdminService")
    def test_delete_event_success(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.delete_event.return_value = None

        response = client.delete("/api/admin/events/1")
        assert response.status_code == 200
        assert response.json()["message"] == "Event deleted successfully"
        mock_service.delete_event.assert_called_once_with(1)

    @patch("src.routers.admin.AdminService")
    def test_delete_event_not_found(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.delete_event.side_effect = HTTPException(
            status_code=404, detail="Event not found"
        )

        response = client.delete("/api/admin/events/999")
        assert response.status_code == 404

    @patch("src.routers.admin.AdminService")
    def test_get_event_registrations_success(self, mock_service_cls, client):
        from schemas.admin import EventRegistrationDetailResponse

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.get_event_registrations.return_value = [
            EventRegistrationDetailResponse(
                id=1,
                event_id=1,
                user_id=1,
                guest_id=None,
                handicap="10",
                email="player@test.com",
                phone="5551234567",
                payment_status="pending",
                payment_method=None,
                amount_paid=None,
            ),
            EventRegistrationDetailResponse(
                id=2,
                event_id=1,
                user_id=2,
                guest_id=None,
                handicap="15",
                email="player2@test.com",
                phone="5559876543",
                payment_status="paid",
                payment_method="card",
                amount_paid=Decimal("50.00"),
            ),
        ]

        response = client.get("/api/admin/events/1/registrations")
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == 1
        assert len(data["registrations"]) == 2
        assert data["registrations"][0]["payment_status"] == "pending"
        assert data["registrations"][1]["payment_status"] == "paid"

    @patch("src.routers.admin.AdminService")
    def test_get_event_registrations_not_found(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.get_event_registrations.side_effect = HTTPException(
            status_code=404, detail="Event not found"
        )

        response = client.get("/api/admin/events/999/registrations")
        assert response.status_code == 404

    @patch("src.routers.admin.AdminService")
    def test_get_event_registrations_empty(self, mock_service_cls, client):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.get_event_registrations.return_value = []

        response = client.get("/api/admin/events/1/registrations")
        assert response.status_code == 200
        data = response.json()
        assert data["registrations"] == []


# ── Admin Banner Tests ────────────────────────────────────────────────────────


class TestAdminBanners:
    """Test admin banner message endpoints."""

    @patch("src.routers.admin.AdminService")
    def test_update_banners_success(self, mock_service_cls, client):
        from schemas.admin import BannerMessageResponse

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.update_banner_messages.return_value = [
            BannerMessageResponse(id=1, message="Welcome to Saga Golf!"),
            BannerMessageResponse(id=2, message="Next event: June 15th"),
        ]

        payload = {
            "messages": [
                {"message": "Welcome to Saga Golf!"},
                {"message": "Next event: June 15th"},
            ]
        }
        response = client.put("/api/admin/banner-messages", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Banner messages updated successfully"
        assert len(data["banners"]) == 2
        assert data["banners"][0]["message"] == "Welcome to Saga Golf!"

    @patch("src.routers.admin.AdminService")
    def test_update_banners_empty_list(self, mock_service_cls, client):

        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service
        mock_service.update_banner_messages.return_value = []

        response = client.put("/api/admin/banner-messages", json={"messages": []})
        assert response.status_code == 200
        data = response.json()
        assert data["banners"] == []

    @patch("src.routers.admin.AdminService")
    def test_update_banners_validation_error(self, mock_service_cls, client):
        # Missing 'messages' key
        response = client.put("/api/admin/banner-messages", json={})
        assert response.status_code == 422


# ── Admin Service Unit Tests ──────────────────────────────────────────────────


class TestAdminService:
    """Test AdminService business logic with mocked repository."""

    @patch("src.services.admin_service.AdminRepository")
    def test_get_all_users(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_all_users.return_value = [_make_user(), _make_non_admin_user()]

        service = AdminService(mock_db)
        result = service.get_all_users()

        assert len(result) == 2
        assert result[0].role == "admin"
        assert result[1].role == "user"

    @patch("src.services.admin_service.AdminRepository")
    def test_update_user_role_user_not_found(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_user_by_id.return_value = None

        service = AdminService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            service.update_user_role(999, "admin")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

    @patch("src.services.admin_service.AdminRepository")
    def test_update_user_role_account_not_found(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_user_by_id.return_value = _make_user()
        mock_repo.get_user_account_by_user_id.return_value = None

        service = AdminService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            service.update_user_role(1, "admin")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User account not found"

    @patch("src.services.admin_service.AdminRepository")
    def test_update_user_role_success(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        user = _make_user(role="user")
        account = user.account
        mock_repo.get_user_by_id.return_value = user
        mock_repo.get_user_account_by_user_id.return_value = account

        service = AdminService(mock_db)
        result = service.update_user_role(1, "admin")

        mock_repo.update_user_role.assert_called_once_with(account, "admin")
        mock_repo.commit.assert_called_once()
        assert result.id == 1

    @patch("src.services.admin_service.AdminRepository")
    def test_delete_user_not_found(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_user_by_id.return_value = None

        service = AdminService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            service.delete_user(999)
        assert exc_info.value.status_code == 404

    @patch("src.services.admin_service.AdminRepository")
    def test_delete_user_success_with_account(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        user = _make_user()
        account = user.account
        mock_repo.get_user_by_id.return_value = user
        mock_repo.get_user_account_by_user_id.return_value = account

        service = AdminService(mock_db)
        service.delete_user(1)

        mock_repo.delete_user_account.assert_called_once_with(account)
        mock_repo.delete_user.assert_called_once_with(user)
        mock_repo.commit.assert_called_once()

    @patch("src.services.admin_service.AdminRepository")
    def test_delete_user_success_without_account(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        user = _make_user()
        mock_repo.get_user_by_id.return_value = user
        mock_repo.get_user_account_by_user_id.return_value = None

        service = AdminService(mock_db)
        service.delete_user(1)

        mock_repo.delete_user_account.assert_not_called()
        mock_repo.delete_user.assert_called_once_with(user)
        mock_repo.commit.assert_called_once()

    @patch("src.services.admin_service.AdminRepository")
    def test_create_event_success(self, mock_repo_cls, mock_db):
        from schemas.admin import CreateEventRequest
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        event = _make_event()
        mock_repo.create_event.return_value = event

        service = AdminService(mock_db)
        data = CreateEventRequest(
            township="Springfield",
            state="IL",
            zipcode="62701",
            golf_course="Lincoln Greens",
            date=date(2026, 6, 15),
            start_time=time(8, 0),
        )
        result = service.create_event(data)

        mock_repo.create_event.assert_called_once()
        mock_repo.commit.assert_called_once()
        assert result.township == "Springfield"

    @patch("src.services.admin_service.AdminRepository")
    def test_update_event_not_found(self, mock_repo_cls, mock_db):
        from schemas.admin import UpdateEventRequest
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_event_by_id.return_value = None

        service = AdminService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            service.update_event(999, UpdateEventRequest(township="New"))
        assert exc_info.value.status_code == 404

    @patch("src.services.admin_service.AdminRepository")
    def test_update_event_success(self, mock_repo_cls, mock_db):
        from schemas.admin import UpdateEventRequest
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        event = _make_event()
        mock_repo.get_event_by_id.return_value = event

        service = AdminService(mock_db)
        result = service.update_event(1, UpdateEventRequest(township="New Town"))

        mock_repo.commit.assert_called_once()
        assert result.township == "New Town"

    @patch("src.services.admin_service.AdminRepository")
    def test_delete_event_not_found(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_event_by_id.return_value = None

        service = AdminService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            service.delete_event(999)
        assert exc_info.value.status_code == 404

    @patch("src.services.admin_service.AdminRepository")
    def test_delete_event_success(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        event = _make_event()
        mock_repo.get_event_by_id.return_value = event

        service = AdminService(mock_db)
        service.delete_event(1)

        mock_repo.delete_event.assert_called_once_with(event)
        mock_repo.commit.assert_called_once()

    @patch("src.services.admin_service.AdminRepository")
    def test_get_event_registrations_event_not_found(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.get_event_by_id.return_value = None

        service = AdminService(mock_db)
        with pytest.raises(HTTPException) as exc_info:
            service.get_event_registrations(999)
        assert exc_info.value.status_code == 404

    @patch("src.services.admin_service.AdminRepository")
    def test_get_event_registrations_success(self, mock_repo_cls, mock_db):
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        event = _make_event()
        mock_repo.get_event_by_id.return_value = event
        mock_repo.get_event_registrations.return_value = [
            _make_registration(1, 1, 1),
            _make_registration(2, 1, 2),
        ]

        service = AdminService(mock_db)
        result = service.get_event_registrations(1)

        assert len(result) == 2
        assert result[0].email == "player@test.com"

    @patch("src.services.admin_service.AdminRepository")
    def test_update_banner_messages_success(self, mock_repo_cls, mock_db):
        from schemas.admin import UpdateBannerMessagesRequest
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        banner1 = _make_banner(1, "Hello")
        banner2 = _make_banner(2, "World")
        mock_repo.create_banner.side_effect = [banner1, banner2]

        service = AdminService(mock_db)
        data = UpdateBannerMessagesRequest(messages=[{"message": "Hello"}, {"message": "World"}])
        result = service.update_banner_messages(data)

        mock_repo.delete_all_banners.assert_called_once()
        assert mock_repo.create_banner.call_count == 2
        mock_repo.commit.assert_called_once()
        assert len(result) == 2

    @patch("src.services.admin_service.AdminRepository")
    def test_update_banner_messages_empty(self, mock_repo_cls, mock_db):
        from schemas.admin import UpdateBannerMessagesRequest
        from src.services.admin_service import AdminService

        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo

        service = AdminService(mock_db)
        data = UpdateBannerMessagesRequest(messages=[])
        result = service.update_banner_messages(data)

        mock_repo.delete_all_banners.assert_called_once()
        mock_repo.create_banner.assert_not_called()
        mock_repo.commit.assert_called_once()
        assert result == []


# ── Dependency Unit Tests ─────────────────────────────────────────────────────


class TestAdminDependency:
    """Test the get_admin_user dependency directly."""

    def test_admin_user_passes(self, admin_user):
        from src.core.dependencies import get_admin_user

        result = get_admin_user(admin_user)
        assert result == admin_user

    def test_non_admin_user_rejected(self, non_admin_user):
        from src.core.dependencies import get_admin_user

        with pytest.raises(HTTPException) as exc_info:
            get_admin_user(non_admin_user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"

    def test_user_without_account_rejected(self):
        from src.core.dependencies import get_admin_user

        user = MagicMock(spec=User)
        user.account = None

        with pytest.raises(HTTPException) as exc_info:
            get_admin_user(user)
        assert exc_info.value.status_code == 403
