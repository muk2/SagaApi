"""
Unit tests for AuthService.

Tests cover:
- Basic authentication functionality
- Token retrieval
- Service initialization
- Integration with AuthRepository
"""
import pytest
from src.services.auth_service import AuthService


class TestAuthService:
    """Test suite for AuthService class."""

    def test_auth_service_initialization(self):
        """Test that AuthService initializes correctly."""
        service = AuthService()
        assert service is not None
        assert hasattr(service, 'auth_repo')
        assert service.auth_repo is not None

    def test_authenticate_user_returns_token(self):
        """Test that authenticate_user returns a token string."""
        service = AuthService()
        token = service.authenticate_user()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_authenticate_user_calls_repository(self):
        """Test that authenticate_user integrates with AuthRepository."""
        service = AuthService()
        token = service.authenticate_user()

        # Should return the token from repository
        assert token == "fake token"

    def test_multiple_auth_service_instances(self):
        """Test that multiple AuthService instances work independently."""
        service1 = AuthService()
        service2 = AuthService()

        token1 = service1.authenticate_user()
        token2 = service2.authenticate_user()

        assert token1 == token2  # Currently returns same token
        assert service1.auth_repo is not service2.auth_repo  # Different repo instances

    def test_auth_service_repository_type(self):
        """Test that AuthService has the correct repository type."""
        service = AuthService()
        # Check that auth_repo has the get_token method (duck typing)
        assert hasattr(service.auth_repo, 'get_token')
        assert callable(service.auth_repo.get_token)
        # Verify it returns the expected token
        assert service.auth_repo.get_token() == "fake token"


class TestAuthServiceEdgeCases:
    """Test suite for AuthService edge cases and error handling."""

    def test_authenticate_user_consistency(self):
        """Test that authenticate_user returns consistent results."""
        service = AuthService()

        token1 = service.authenticate_user()
        token2 = service.authenticate_user()
        token3 = service.authenticate_user()

        # Should be consistent (currently returns same fake token)
        assert token1 == token2 == token3

    def test_auth_service_str_representation(self):
        """Test that AuthService can be converted to string without error."""
        service = AuthService()
        str_repr = str(service)
        assert str_repr is not None

    def test_auth_service_attribute_access(self):
        """Test that AuthService attributes are accessible."""
        service = AuthService()

        # Should be able to access auth_repo
        repo = service.auth_repo
        assert repo is not None

        # Should be able to call authenticate_user
        assert callable(service.authenticate_user)
