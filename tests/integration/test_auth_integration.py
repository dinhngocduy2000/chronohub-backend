"""
Integration tests for Authentication with Group endpoints

These tests verify that authentication middleware works correctly
with actual HTTP endpoints. Unlike test_group_endpoints.py which mocks
auth, these tests use real authentication middleware.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import jwt

from app.handler.group import GroupHandler
from app.router.group import GroupRouter
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.user import UserInfo
from app.common.enum.user_status import UserStatus
from app.core.config import settings


@pytest.fixture
def real_auth_app(mock_group_service, mock_auth_service):
    """
    Create a test app WITH real authentication middleware
    (not mocked via dependency override)
    """
    app = FastAPI()
    
    # Initialize auth middleware with mock service
    AuthMiddleware.init(mock_auth_service)
    
    # Create handler and router
    group_handler = GroupHandler(service=mock_group_service)
    group_router = GroupRouter(handler=group_handler)
    
    # Include router
    app.include_router(
        group_router.router,
        prefix="/api/v1/groups",
        tags=["Groups"],
    )
    
    return app


@pytest.fixture
def real_auth_client(real_auth_app):
    """TestClient that uses real authentication"""
    # raise_server_exceptions=False allows us to test error responses
    return TestClient(real_auth_app, raise_server_exceptions=False)


class TestAuthenticationIntegration:
    """Test authentication middleware integration with endpoints"""
    
    # ========== VALID AUTHENTICATION ==========
    
    def test_endpoint_with_valid_token_succeeds(
        self,
        real_auth_client,
        mock_group_service,
        mock_auth_service,
        valid_jwt_token,
        mock_credential,
        sample_group_info
    ):
        """
        GIVEN a valid JWT token in cookies
        WHEN making request to protected endpoint
        THEN request should succeed with 201
        """
        # Arrange
        user_info = UserInfo(
            id=mock_credential.id,
            name="Test User",
            email=mock_credential.email,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        mock_group_service.create_group.return_value = sample_group_info
        
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act - Set token in cookies
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}  # Real token!
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["name"] == "Test Group"
        mock_auth_service.get_current_user.assert_called_once()
    
    def test_endpoint_with_valid_token_for_pending_user_succeeds(
        self,
        real_auth_client,
        mock_group_service,
        mock_auth_service,
        valid_jwt_token,
        mock_credential,
        sample_group_info
    ):
        """
        GIVEN a valid token for a pending user
        WHEN making request to protected endpoint
        THEN request should succeed (endpoint allows pending users)
        """
        # Arrange
        pending_user = UserInfo(
            id=mock_credential.id,
            name="Pending User",
            email=mock_credential.email,
            status=UserStatus.PENDING,  # Pending!
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = pending_user
        mock_group_service.create_group.return_value = sample_group_info
        
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}
        )
        
        # Assert
        assert response.status_code == 201
    
    # ========== NO AUTHENTICATION ==========
    
    def test_endpoint_without_token_returns_401(
        self,
        real_auth_client,
        mock_auth_service
    ):
        """
        GIVEN no authentication token
        WHEN making request to protected endpoint
        THEN should return 401 Unauthorized
        """
        # Arrange
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act - No cookies provided!
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data
            # No cookies parameter = no token
        )
        
        # Assert
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
        mock_auth_service.get_current_user.assert_not_called()
    
    def test_endpoint_with_empty_cookie_returns_401(
        self,
        real_auth_client,
        mock_auth_service
    ):
        """
        GIVEN empty cookies dictionary
        WHEN making request to protected endpoint
        THEN should return 401 Unauthorized
        """
        # Arrange
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act - Empty cookies
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={}  # Empty cookies
        )
        
        # Assert
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
    
    # ========== EXPIRED TOKEN ==========
    
    def test_endpoint_with_expired_token_returns_error(
        self,
        real_auth_client,
        mock_auth_service,
        expired_jwt_token
    ):
        """
        GIVEN an expired JWT token
        WHEN making request to protected endpoint
        THEN JWT library raises ExpiredSignatureError (caught by FastAPI)
        """
        # Arrange
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": expired_jwt_token}
        )
        
        # Assert
        # FastAPI catches the JWT error and returns 500
        assert response.status_code == 500
        mock_auth_service.get_current_user.assert_not_called()
    
    # ========== INVALID TOKEN ==========
    
    def test_endpoint_with_invalid_token_format_returns_error(
        self,
        real_auth_client,
        mock_auth_service
    ):
        """
        GIVEN an invalid JWT token (malformed)
        WHEN making request to protected endpoint
        THEN should return error (JWT decode fails)
        """
        # Arrange
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act - Invalid token format
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": "invalid.jwt.token"}
        )
        
        # Assert
        assert response.status_code == 500  # JWT decode error
        mock_auth_service.get_current_user.assert_not_called()
    
    def test_endpoint_with_wrong_secret_token_returns_error(
        self,
        real_auth_client,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a token signed with wrong secret
        WHEN making request to protected endpoint
        THEN JWT signature verification fails
        """
        # Arrange
        wrong_secret_token = jwt.encode(
            {
                "id": str(mock_credential.id),
                "email": mock_credential.email,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            },
            "wrong_secret_key",  # Wrong secret!
            algorithm=settings.ALGORITHM
        )
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": wrong_secret_token}
        )
        
        # Assert
        assert response.status_code == 500  # Signature verification failed
        mock_auth_service.get_current_user.assert_not_called()
    
    # ========== USER NOT FOUND ==========
    
    def test_endpoint_with_valid_token_but_user_not_found_returns_401(
        self,
        real_auth_client,
        mock_auth_service,
        valid_jwt_token
    ):
        """
        GIVEN a valid token but user doesn't exist in database
        WHEN making request to protected endpoint
        THEN should return 401 Unauthorized
        """
        # Arrange
        mock_auth_service.get_current_user.return_value = None  # User not found!
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}
        )
        
        # Assert
        assert response.status_code == 401
        assert response.json()["detail"] == "Unauthorized"
        mock_auth_service.get_current_user.assert_called_once()
    
    # ========== TOKEN STRUCTURE ISSUES ==========
    
    def test_endpoint_with_token_missing_user_id_returns_error(
        self,
        real_auth_client,
        mock_auth_service
    ):
        """
        GIVEN a token without user ID field
        WHEN making request to protected endpoint
        THEN should return error (KeyError)
        """
        # Arrange
        token_without_id = jwt.encode(
            {
                # Missing 'id' field
                "email": "test@example.com",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": token_without_id}
        )
        
        # Assert
        assert response.status_code == 500  # KeyError during processing
        mock_auth_service.get_current_user.assert_not_called()
    
    # ========== MULTIPLE REQUESTS ==========
    
    def test_multiple_requests_with_same_token_all_succeed(
        self,
        real_auth_client,
        mock_group_service,
        mock_auth_service,
        valid_jwt_token,
        mock_credential,
        sample_group_info
    ):
        """
        GIVEN a valid token
        WHEN making multiple requests with same token
        THEN all requests should succeed
        """
        # Arrange
        user_info = UserInfo(
            id=mock_credential.id,
            name="Test User",
            email=mock_credential.email,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        mock_group_service.create_group.return_value = sample_group_info
        
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act - Make 3 requests with same token
        response1 = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}
        )
        
        response2 = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}
        )
        
        response3 = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}
        )
        
        # Assert - All should succeed
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response3.status_code == 201
        assert mock_auth_service.get_current_user.call_count == 3
    
    # ========== EDGE CASES ==========
    
    def test_endpoint_with_almost_expired_token_succeeds(
        self,
        real_auth_client,
        mock_group_service,
        mock_auth_service,
        mock_credential,
        sample_group_info
    ):
        """
        GIVEN a token expiring in 5 seconds
        WHEN making request before expiration
        THEN request should succeed
        """
        # Arrange
        almost_expired_token = jwt.encode(
            {
                "id": str(mock_credential.id),
                "email": mock_credential.email,
                "exp": datetime.now(timezone.utc) + timedelta(seconds=5),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        user_info = UserInfo(
            id=mock_credential.id,
            name="Test User",
            email=mock_credential.email,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        mock_group_service.create_group.return_value = sample_group_info
        
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": almost_expired_token}
        )
        
        # Assert
        assert response.status_code == 201
    
    def test_endpoint_when_auth_service_raises_exception_returns_500(
        self,
        real_auth_client,
        mock_auth_service,
        valid_jwt_token
    ):
        """
        GIVEN a valid token but auth service throws exception
        WHEN making request to protected endpoint
        THEN should return 500 (exception propagates)
        """
        # Arrange
        mock_auth_service.get_current_user.side_effect = Exception("Database error")
        request_data = {"name": "Test Group", "description": "Test"}
        
        # Act
        response = real_auth_client.post(
            "/api/v1/groups/create",
            json=request_data,
            cookies={"access_token": valid_jwt_token}
        )
        
        # Assert
        assert response.status_code == 500
        mock_auth_service.get_current_user.assert_called_once()


class TestAuthenticationWithDifferentEndpoints:
    """Test authentication works consistently across different endpoints"""
    
    def test_auth_required_for_all_group_endpoints(
        self,
        real_auth_client
    ):
        """
        GIVEN no authentication
        WHEN accessing any protected endpoint
        THEN all should return 401
        """
        # All these endpoints should require auth
        endpoints = [
            ("/api/v1/groups/create", "POST", {"name": "Test"}),
            # Add more endpoints as they're implemented
        ]
        
        for path, method, data in endpoints:
            if method == "POST":
                response = real_auth_client.post(path, json=data)
            elif method == "GET":
                response = real_auth_client.get(path)
            
            # All should return 401 without auth
            assert response.status_code == 401, f"{method} {path} should require auth"
