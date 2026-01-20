"""
Error handling and negative test cases for authentication system.

Tests cover:
- Repository stress testing
- Fixture validation
- Token consistency
- Edge cases with current implementation
"""
import pytest
from src.services.auth_service import AuthService
from src.repositories.auth_repository import AuthRepository


class TestAuthServiceRobustness:
    """Test suite for AuthService robustness."""

    def test_auth_service_multiple_calls_consistency(self):
        """Test that service returns consistent tokens across many calls."""
        service = AuthService()

        tokens = [service.authenticate_user() for _ in range(50)]

        # All should be identical
        assert all(t == tokens[0] for t in tokens)
        assert len(set(tokens)) == 1  # Only one unique token

    def test_auth_service_repository_always_available(self):
        """Test that service always has an accessible repository."""
        service = AuthService()

        # Repository should always be available
        assert service.auth_repo is not None

        # Should work even after many calls
        for _ in range(10):
            token = service.authenticate_user()
            assert token is not None
            assert service.auth_repo is not None


class TestAuthRepositoryErrorHandling:
    """Test suite for AuthRepository error scenarios."""

    def test_auth_repository_consistency_under_load(self):
        """Test repository behavior under repeated calls."""
        repo = AuthRepository()

        # Call get_token many times rapidly
        tokens = [repo.get_token() for _ in range(100)]

        # Should all be consistent
        assert all(t == "fake token" for t in tokens)
        assert len(tokens) == 100

    def test_auth_repository_no_side_effects(self):
        """Test that get_token has no side effects."""
        repo = AuthRepository()

        # Get token multiple times
        token1 = repo.get_token()
        token2 = repo.get_token()
        token3 = repo.get_token()

        # Should not modify state or have side effects
        assert token1 == token2 == token3

    def test_repository_returns_non_empty_token(self):
        """Test that repository never returns empty token."""
        repo = AuthRepository()

        for _ in range(20):
            token = repo.get_token()
            assert token  # Should be truthy (not empty)
            assert len(token) > 0


class TestAuthIntegrationStress:
    """Test suite for integration stress scenarios."""

    def test_many_services_many_calls(self):
        """Test creating many services and making many calls."""
        services = [AuthService() for _ in range(10)]

        for service in services:
            tokens = [service.authenticate_user() for _ in range(10)]
            # All tokens from same service should be identical
            assert all(t == tokens[0] for t in tokens)

        # All services should return same token (current implementation)
        all_first_tokens = [s.authenticate_user() for s in services]
        assert all(t == "fake token" for t in all_first_tokens)

    def test_service_repository_independence(self):
        """Test that each service has its own repository instance."""
        service1 = AuthService()
        service2 = AuthService()
        service3 = AuthService()

        # Each should have different repository instances
        assert service1.auth_repo is not service2.auth_repo
        assert service2.auth_repo is not service3.auth_repo
        assert service1.auth_repo is not service3.auth_repo

        # But all return same token
        assert service1.authenticate_user() == service2.authenticate_user()
        assert service2.authenticate_user() == service3.authenticate_user()


class TestTokenValidation:
    """Test suite for token validation edge cases using fixtures."""

    def test_invalid_token_fixture(self, invalid_auth_token):
        """Test that invalid token fixture works as expected."""
        assert invalid_auth_token == "invalid_token"
        assert isinstance(invalid_auth_token, str)

    def test_expired_token_fixture(self, expired_auth_token):
        """Test that expired token fixture works as expected."""
        assert expired_auth_token == "expired_token"
        assert isinstance(expired_auth_token, str)

    def test_mock_token_fixture(self, mock_auth_token):
        """Test that mock token fixture works as expected."""
        assert mock_auth_token == "fake token"
        assert isinstance(mock_auth_token, str)

    def test_comparing_token_fixtures(self, mock_auth_token, invalid_auth_token, expired_auth_token):
        """Test that all token fixtures are different."""
        assert mock_auth_token != invalid_auth_token
        assert mock_auth_token != expired_auth_token
        assert invalid_auth_token != expired_auth_token

        # All should be strings
        assert all(isinstance(t, str) for t in [mock_auth_token, invalid_auth_token, expired_auth_token])

    def test_fixtures_can_be_used_in_comparisons(self, mock_auth_token):
        """Test that fixtures work correctly with actual code."""
        service = AuthService()
        actual_token = service.authenticate_user()

        # Should match the mock_auth_token fixture
        assert actual_token == mock_auth_token


class TestAuthSystemBoundaries:
    """Test system boundaries and edge cases."""

    def test_token_is_always_string(self):
        """Test that token is always a string type."""
        service = AuthService()
        repo = AuthRepository()

        service_token = service.authenticate_user()
        repo_token = repo.get_token()

        assert isinstance(service_token, str)
        assert isinstance(repo_token, str)

    def test_token_not_none_or_empty(self):
        """Test that tokens are never None or empty."""
        service = AuthService()

        for _ in range(10):
            token = service.authenticate_user()
            assert token is not None
            assert token != ""
            assert len(token) > 0
