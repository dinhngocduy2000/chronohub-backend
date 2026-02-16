"""
Unit tests for GroupHandler
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.handler.group import GroupHandler
from app.common.schemas.group import GroupCreateDTO


class TestGroupHandler:
    """Test cases for GroupHandler"""

    @pytest.mark.asyncio
    async def test_create_group_success(
        self, 
        mock_group_service, 
        sample_group_create_dto,
        sample_group_info,
        mock_credential
    ):
        """Test successful group creation"""
        # Arrange
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        result = await handler.create_group(
            group_create=sample_group_create_dto,
            credential=mock_credential
        )

        # Assert
        assert result == sample_group_info
        assert result.name == "Test Group"
        mock_group_service.create_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_group_with_exception(
        self, 
        mock_group_service,
        sample_group_create_dto,
        mock_credential
    ):
        """Test group creation with service exception"""
        # Arrange
        from app.common.exceptions import ExceptionInternalError
        mock_group_service.create_group.side_effect = Exception("Database error")
        handler = GroupHandler(service=mock_group_service)

        # Act & Assert
        # The @exception_handler decorator wraps exceptions in ExceptionInternalError
        with pytest.raises(ExceptionInternalError) as exc_info:
            await handler.create_group(
                group_create=sample_group_create_dto,
                credential=mock_credential
            )
        
        assert exc_info.value.status_code == 500
        mock_group_service.create_group.assert_called_once()
