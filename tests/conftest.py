"""
Pytest configuration and fixtures for SagaApi tests.
"""
import pytest


@pytest.fixture
def mock_auth_token():
    """
    Fixture providing a mock authentication token for testing.
    """
    return "fake token"


@pytest.fixture
def invalid_auth_token():
    """
    Fixture providing an invalid authentication token for testing edge cases.
    """
    return "invalid_token"


@pytest.fixture
def expired_auth_token():
    """
    Fixture providing an expired authentication token for testing edge cases.
    """
    return "expired_token"


@pytest.fixture
def auth_service():
    """
    Fixture providing an AuthService instance for testing.
    """
    import sys
    sys.path.insert(0, '/Users/malchal/SagaApi/src')
    from services.auth_service import AuthService
    return AuthService()


@pytest.fixture
def auth_repository():
    """
    Fixture providing an AuthRepository instance for testing.
    """
    import sys
    sys.path.insert(0, '/Users/malchal/SagaApi/src')
    from repositories.auth_repository import AuthRepository
    return AuthRepository()
