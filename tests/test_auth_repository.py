"""
Unit tests for AuthRepository.

Tests cover:
- Token generation/retrieval
- Repository initialization
- Edge cases and error handling
"""
import pytest
from src.repositories.auth_repository import AuthRepository


class TestAuthRepository:
    """Test suite for AuthRepository class."""

    def test_auth_repository_initialization(self):
        """Test that AuthRepository initializes correctly."""
        repo = AuthRepository()
        assert repo is not None

    def test_get_token_returns_string(self):
        """Test that get_token returns a string token."""
        repo = AuthRepository()
        token = repo.get_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_get_token_returns_expected_value(self):
        """Test that get_token returns the expected fake token."""
        repo = AuthRepository()
        token = repo.get_token()

        assert token == "fake token"

    def test_get_token_consistency(self):
        """Test that get_token returns consistent results."""
        repo = AuthRepository()

        token1 = repo.get_token()
        token2 = repo.get_token()
        token3 = repo.get_token()

        assert token1 == token2 == token3

    def test_multiple_repository_instances(self):
        """Test that multiple AuthRepository instances work correctly."""
        repo1 = AuthRepository()
        repo2 = AuthRepository()

        token1 = repo1.get_token()
        token2 = repo2.get_token()

        # Both should return the same fake token
        assert token1 == token2

    def test_auth_repository_has_get_token_method(self):
        """Test that AuthRepository has the get_token method."""
        repo = AuthRepository()
        assert hasattr(repo, 'get_token')
        assert callable(repo.get_token)


class TestAuthRepositoryEdgeCases:
    """Test suite for AuthRepository edge cases."""

    def test_get_token_called_multiple_times(self):
        """Test that get_token can be called multiple times without issues."""
        repo = AuthRepository()

        for _ in range(10):
            token = repo.get_token()
            assert token == "fake token"

    def test_auth_repository_str_representation(self):
        """Test that AuthRepository can be converted to string."""
        repo = AuthRepository()
        str_repr = str(repo)
        assert str_repr is not None

    def test_auth_repository_repr(self):
        """Test that AuthRepository has a repr."""
        repo = AuthRepository()
        repr_str = repr(repo)
        assert repr_str is not None

    def test_get_token_return_type(self):
        """Test that get_token specifically returns str type."""
        repo = AuthRepository()
        token = repo.get_token()

        assert type(token) == str
        assert not isinstance(token, (int, float, bool, dict, list))

    def test_auth_repository_instance_isolation(self):
        """Test that different repository instances are isolated."""
        repo1 = AuthRepository()
        repo2 = AuthRepository()

        # They should be different instances
        assert repo1 is not repo2

        # But return the same token (current implementation)
        assert repo1.get_token() == repo2.get_token()
