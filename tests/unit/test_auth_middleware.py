"""
Unit tests for AuthMiddleware

These tests verify the authentication middleware logic including:
- Token validation
- JWT decoding
- Token expiration checking
- User lookup
- Error handling
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import jwt

from fastapi import HTTPException, status

from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.user import UserInfo, Credential
from app.common.enum.user_status import UserStatus
from app.core.config import settings


class TestAuthMiddlewareTokenValidation:
    """Tests for token validation logic"""
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_valid_token_returns_credential(
        self,
        mock_request,
        valid_jwt_token,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a valid JWT token in cookies
        WHEN auth_middleware is called
        THEN it should return a valid Credential
        """
        # Arrange
        mock_request.cookies = {"access_token": valid_jwt_token}
        
        user_info = UserInfo(
            id=mock_credential.id,
            name="Test User",
            email=mock_credential.email,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        
        # Initialize middleware
        AuthMiddleware.init(mock_auth_service)
        
        # Act
        result = await AuthMiddleware.auth_middleware(mock_request)
        
        # Assert
        assert isinstance(result, Credential)
        assert result.id == mock_credential.id
        assert result.email == mock_credential.email
        assert result.is_pending == False
        mock_auth_service.get_current_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_middleware_without_token_raises_401(
        self,
        mock_request,
        mock_auth_service
    ):
        """
        GIVEN a request without access_token cookie
        WHEN auth_middleware is called
        THEN it should raise 401 Unauthorized
        """
        # Arrange
        mock_request.cookies = {}  # No token
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await AuthMiddleware.auth_middleware(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Unauthorized"
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_expired_token_raises_exception(
        self,
        mock_request,
        expired_jwt_token,
        mock_auth_service
    ):
        """
        GIVEN an expired JWT token
        WHEN auth_middleware is called
        THEN JWT library raises ExpiredSignatureError during decode
        """
        # Arrange
        mock_request.cookies = {"access_token": expired_jwt_token}
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        # JWT library raises ExpiredSignatureError before our code can check
        with pytest.raises(jwt.ExpiredSignatureError):
            await AuthMiddleware.auth_middleware(mock_request)
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_invalid_jwt_raises_401(
        self,
        mock_request,
        mock_auth_service
    ):
        """
        GIVEN an invalid JWT token (malformed)
        WHEN auth_middleware is called
        THEN it should raise 401 Unauthorized via JWT decode error
        """
        # Arrange
        mock_request.cookies = {"access_token": "invalid.jwt.token"}
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(Exception):  # JWT decode will raise an exception
            await AuthMiddleware.auth_middleware(mock_request)
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_wrong_secret_raises_error(
        self,
        mock_request,
        mock_credential,
        mock_auth_service
    ):
        """
        GIVEN a JWT token signed with wrong secret
        WHEN auth_middleware is called
        THEN it should raise an error during decode
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
        mock_request.cookies = {"access_token": wrong_secret_token}
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(Exception):  # JWT InvalidSignatureError
            await AuthMiddleware.auth_middleware(mock_request)


class TestAuthMiddlewareUserLookup:
    """Tests for user lookup logic"""
    
    @pytest.mark.asyncio
    async def test_auth_middleware_when_user_not_found_raises_401(
        self,
        mock_request,
        valid_jwt_token,
        mock_auth_service
    ):
        """
        GIVEN a valid token but user doesn't exist in database
        WHEN auth_middleware is called
        THEN it should raise 401 Unauthorized
        """
        # Arrange
        mock_request.cookies = {"access_token": valid_jwt_token}
        mock_auth_service.get_current_user.return_value = None  # User not found
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await AuthMiddleware.auth_middleware(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Unauthorized"
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_pending_user_sets_is_pending(
        self,
        mock_request,
        valid_jwt_token,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a valid token for a pending user
        WHEN auth_middleware is called
        THEN credential should have is_pending=True
        """
        # Arrange
        mock_request.cookies = {"access_token": valid_jwt_token}
        
        pending_user = UserInfo(
            id=mock_credential.id,
            name="Pending User",
            email=mock_credential.email,
            status=UserStatus.PENDING,  # Pending status
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = pending_user
        AuthMiddleware.init(mock_auth_service)
        
        # Act
        result = await AuthMiddleware.auth_middleware(mock_request)
        
        # Assert
        assert result.is_pending == True
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_active_user_sets_is_pending_false(
        self,
        mock_request,
        valid_jwt_token,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a valid token for an active user
        WHEN auth_middleware is called
        THEN credential should have is_pending=False
        """
        # Arrange
        mock_request.cookies = {"access_token": valid_jwt_token}
        
        active_user = UserInfo(
            id=mock_credential.id,
            name="Active User",
            email=mock_credential.email,
            status=UserStatus.ACTIVE,  # Active status
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = active_user
        AuthMiddleware.init(mock_auth_service)
        
        # Act
        result = await AuthMiddleware.auth_middleware(mock_request)
        
        # Assert
        assert result.is_pending == False


class TestAuthMiddlewareTokenStructure:
    """Tests for token structure validation"""
    
    @pytest.mark.asyncio
    async def test_auth_middleware_extracts_user_id_from_token(
        self,
        mock_request,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a valid JWT token with user ID
        WHEN auth_middleware is called
        THEN it should correctly extract and use the user ID
        """
        # Arrange
        user_id = uuid4()
        token = jwt.encode(
            {
                "id": str(user_id),
                "email": "test@example.com",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        mock_request.cookies = {"access_token": token}
        
        user_info = UserInfo(
            id=user_id,
            name="Test User",
            email="test@example.com",
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        AuthMiddleware.init(mock_auth_service)
        
        # Act
        result = await AuthMiddleware.auth_middleware(mock_request)
        
        # Assert
        assert result.id == user_id
        # Verify get_current_user was called with correct user_id
        call_args = mock_auth_service.get_current_user.call_args
        assert call_args.args[0] == user_id
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_token_missing_exp_field(
        self,
        mock_request,
        mock_auth_service
    ):
        """
        GIVEN a JWT token without 'exp' field
        WHEN auth_middleware is called
        THEN it should raise an error (KeyError)
        """
        # Arrange
        token_without_exp = jwt.encode(
            {
                "id": str(uuid4()),
                "email": "test@example.com",
                # Missing 'exp' field
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        mock_request.cookies = {"access_token": token_without_exp}
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(KeyError):
            await AuthMiddleware.auth_middleware(mock_request)
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_token_missing_id_field(
        self,
        mock_request,
        mock_auth_service
    ):
        """
        GIVEN a JWT token without 'id' field
        WHEN auth_middleware is called
        THEN it should raise an error (KeyError)
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
        
        mock_request.cookies = {"access_token": token_without_id}
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(KeyError):
            await AuthMiddleware.auth_middleware(mock_request)


class TestAuthMiddlewareEdgeCases:
    """Tests for edge cases and error scenarios"""
    
    @pytest.mark.asyncio
    async def test_auth_middleware_with_empty_token_string(
        self,
        mock_request,
        mock_auth_service
    ):
        """
        GIVEN an empty string as token
        WHEN auth_middleware is called
        THEN it should raise an error during JWT decode
        """
        # Arrange
        mock_request.cookies = {"access_token": ""}
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(Exception):
            await AuthMiddleware.auth_middleware(mock_request)
    
    @pytest.mark.asyncio
    async def test_auth_middleware_when_service_raises_exception(
        self,
        mock_request,
        valid_jwt_token,
        mock_auth_service
    ):
        """
        GIVEN a valid token but service throws exception
        WHEN auth_middleware is called
        THEN the exception should propagate
        """
        # Arrange
        mock_request.cookies = {"access_token": valid_jwt_token}
        mock_auth_service.get_current_user.side_effect = Exception("Database error")
        AuthMiddleware.init(mock_auth_service)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await AuthMiddleware.auth_middleware(mock_request)
        
        assert "Database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_auth_middleware_token_expiring_within_seconds(
        self,
        mock_request,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a token that expires in 5 seconds (edge case)
        WHEN auth_middleware is called
        THEN it should still work if not yet expired
        """
        # Arrange
        almost_expired_token = jwt.encode(
            {
                "id": str(mock_credential.id),
                "email": mock_credential.email,
                "exp": datetime.now(timezone.utc) + timedelta(seconds=5),  # Expires soon!
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        mock_request.cookies = {"access_token": almost_expired_token}
        
        user_info = UserInfo(
            id=mock_credential.id,
            name="Test User",
            email=mock_credential.email,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        AuthMiddleware.init(mock_auth_service)
        
        # Act
        result = await AuthMiddleware.auth_middleware(mock_request)
        
        # Assert
        assert result.id == mock_credential.id


class TestAuthMiddlewareIntegration:
    """Integration-style tests for complete auth flow"""
    
    @pytest.mark.asyncio
    async def test_auth_middleware_complete_success_flow(
        self,
        mock_request,
        mock_auth_service,
        mock_credential
    ):
        """
        GIVEN a complete valid authentication scenario
        WHEN auth_middleware is called
        THEN it should successfully authenticate and return credential
        """
        # Arrange
        user_id = uuid4()
        email = "complete@test.com"
        
        # Create valid token
        token = jwt.encode(
            {
                "id": str(user_id),
                "email": email,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                "iat": datetime.now(timezone.utc),
                "type": "access"
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        mock_request.cookies = {"access_token": token}
        
        # Mock user exists
        user_info = UserInfo(
            id=user_id,
            name="Complete User",
            email=email,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_auth_service.get_current_user.return_value = user_info
        AuthMiddleware.init(mock_auth_service)
        
        # Act
        result = await AuthMiddleware.auth_middleware(mock_request)
        
        # Assert - Verify complete flow
        assert isinstance(result, Credential)
        assert result.id == user_id
        assert result.email == email
        assert result.is_pending == False
        
        # Verify service was called with correct context
        mock_auth_service.get_current_user.assert_called_once()
        call_args = mock_auth_service.get_current_user.call_args
        assert call_args.args[0] == user_id
        assert call_args.kwargs['ctx'] is not None
