"""
Pytest configuration and fixtures for testing
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.common.schemas.user import Credential, UserInfo
from app.common.schemas.group import GroupInfo, GroupCreateDTO
from app.handler.group import GroupHandler
from app.router.group import GroupRouter


@pytest.fixture
def mock_credential():
    """Mock authenticated user credential"""
    return Credential(
        id=uuid4(),
        email="testuser@example.com",
        name="Test User"
    )


@pytest.fixture
def sample_group_create_dto():
    """Sample group creation data"""
    return GroupCreateDTO(
        name="Test Group",
        description="Test Description",
        members=[]
    )


@pytest.fixture
def sample_group_info():
    """Sample group info response"""
    user = UserInfo(
        id=uuid4(),
        email="testuser@example.com",
        name="Test User"
    )
    
    return GroupInfo(
        id=uuid4(),
        name="Test Group",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        members=[user]
    )


@pytest.fixture
def mock_group_service():
    """Mock GroupService"""
    service = Mock()
    service.create_group = AsyncMock()
    return service


@pytest.fixture
def mock_repo():
    """Mock Repository Registry"""
    repo = Mock()
    repo.group_repo = Mock()
    repo.transaction_wrapper = AsyncMock()
    return repo


@pytest.fixture
def mock_session():
    """Mock AsyncSession"""
    return AsyncMock()


@pytest.fixture
def test_app(mock_group_service, mock_credential):
    """
    Create a test FastAPI app with mocked dependencies
    
    This fixture creates a minimal FastAPI app for testing endpoints
    without requiring database connections or real services.
    """
    from fastapi import Depends
    from app.common.middleware.auth_middleware import AuthMiddleware
    
    app = FastAPI()
    
    # Override the auth middleware dependency
    async def mock_auth_middleware():
        return mock_credential
    
    # Create handler with mocked service
    group_handler = GroupHandler(service=mock_group_service)
    
    # Create router with mocked handler
    group_router = GroupRouter(handler=group_handler)
    
    # Include router in app
    app.include_router(
        group_router.router,
        prefix="/api/v1/groups",
        tags=["Groups"],
    )
    
    # Override the authentication dependency
    app.dependency_overrides[AuthMiddleware.auth_middleware] = mock_auth_middleware
    
    return app


@pytest.fixture
def test_client(test_app):
    """
    Create a TestClient for making requests to the test app
    
    Usage:
        def test_endpoint(test_client):
            response = test_client.post("/api/v1/groups/create", json={...})
            assert response.status_code == 201
    """
    return TestClient(test_app)


@pytest.fixture
def auth_headers(mock_credential):
    """
    Mock authorization headers for authenticated requests
    
    Usage:
        def test_protected_endpoint(test_client, auth_headers):
            response = test_client.get("/protected", headers=auth_headers)
    """
    # In a real scenario, you'd generate a JWT token here
    # For testing, we'll use a simple mock token
    return {
        "Authorization": "Bearer mock_token_for_testing"
    }


# ============= Auth Middleware Fixtures =============

@pytest.fixture
def mock_request():
    """Mock FastAPI Request object"""
    request = Mock()
    request.cookies = {}
    return request


@pytest.fixture
def valid_jwt_token(mock_credential):
    """Generate a valid JWT token for testing"""
    from datetime import datetime, timedelta, timezone
    import jwt
    from app.core.config import settings
    
    payload = {
        "id": str(mock_credential.id),
        "email": mock_credential.email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def expired_jwt_token(mock_credential):
    """Generate an expired JWT token for testing"""
    from datetime import datetime, timedelta, timezone
    import jwt
    from app.core.config import settings
    
    payload = {
        "id": str(mock_credential.id),
        "email": mock_credential.email,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=30),  # Expired!
        "iat": datetime.now(timezone.utc) - timedelta(minutes=60),
        "type": "access"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


@pytest.fixture
def mock_auth_service():
    """Mock AuthService for middleware testing"""
    service = Mock()
    service.get_current_user = AsyncMock()
    return service
