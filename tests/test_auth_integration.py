"""
Integration tests for authentication system.

Tests cover:
- Integration between AuthService and AuthRepository
- End-to-end authentication flows
- System behavior under various conditions
"""
import pytest
from src.services.auth_service import AuthService
from src.repositories.auth_repository import AuthRepository


class TestAuthIntegration:
    """Integration tests for authentication components."""

    def test_service_repository_integration(self):
        """Test that AuthService correctly integrates with AuthRepository."""
        service = AuthService()
        repo = AuthRepository()

        service_token = service.authenticate_user()
        repo_token = repo.get_token()

        # Service should get token from repository
        assert service_token == repo_token

    def test_authentication_flow_end_to_end(self):
        """Test complete authentication flow from service to repository."""
        # Step 1: Create service
        service = AuthService()
        assert service is not None

        # Step 2: Authenticate user
        token = service.authenticate_user()
        assert token is not None

        # Step 3: Verify token format
        assert isinstance(token, str)
        assert len(token) > 0

    def test_multiple_authentications(self):
        """Test multiple authentication requests."""
        service = AuthService()

        tokens = []
        for i in range(5):
            token = service.authenticate_user()
            tokens.append(token)

        # All tokens should be present
        assert len(tokens) == 5

        # All tokens should be identical (current implementation)
        assert all(t == tokens[0] for t in tokens)

    def test_service_uses_repository_instance(self):
        """Test that service creates and uses its own repository instance."""
        service = AuthService()

        # Service should have a repository
        assert hasattr(service, 'auth_repo')
        assert service.auth_repo is not None

        # Repository should be of correct type
        assert isinstance(service.auth_repo, AuthRepository)

        # Service's repo should work
        token = service.auth_repo.get_token()
        assert token == "fake token"

    def test_isolated_service_instances(self):
        """Test that different service instances are properly isolated."""
        service1 = AuthService()
        service2 = AuthService()

        # Services should be different
        assert service1 is not service2

        # Repositories should be different
        assert service1.auth_repo is not service2.auth_repo

        # But tokens should be the same (current implementation)
        assert service1.authenticate_user() == service2.authenticate_user()


class TestAuthIntegrationEdgeCases:
    """Integration tests for edge cases and error scenarios."""

    def test_repository_dependency_injection(self):
        """Test that service correctly initializes its repository dependency."""
        service = AuthService()

        # Verify repository was injected/created
        assert service.auth_repo is not None

        # Verify we can access repository methods through service
        direct_token = service.auth_repo.get_token()
        service_token = service.authenticate_user()

        assert direct_token == service_token

    def test_authentication_without_explicit_repo_creation(self):
        """Test that authentication works without manually creating repository."""
        # Just create service, repository should be auto-created
        service = AuthService()

        # Should work without explicitly creating AuthRepository
        token = service.authenticate_user()

        assert token == "fake token"

    def test_concurrent_service_usage(self):
        """Test multiple services being used concurrently."""
        services = [AuthService() for _ in range(3)]

        tokens = [s.authenticate_user() for s in services]

        # All should return tokens
        assert all(t is not None for t in tokens)

        # All should return the same token (current implementation)
        assert all(t == "fake token" for t in tokens)

    def test_service_repository_relationship(self):
        """Test the relationship between service and repository."""
        service = AuthService()

        # Service should own its repository
        repo = service.auth_repo

        # Modifying service shouldn't affect other instances
        service2 = AuthService()
        assert service2.auth_repo is not repo
