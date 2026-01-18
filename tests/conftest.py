"""
Pytest configuration and fixtures for SagaApi tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """
    Fixture providing a TestClient for FastAPI application.

    Usage:
        def test_endpoint(client):
            response = client.get("/some-endpoint")
            assert response.status_code == 200
    """
    return TestClient(app)


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
