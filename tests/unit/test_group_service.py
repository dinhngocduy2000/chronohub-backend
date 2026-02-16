"""
Unit tests for GroupService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.group import GroupService
from app.common.schemas.group import GroupCreateDTO, GroupQuery
from app.common.exceptions import BadRequestException


class TestGroupService:
    """Test cases for GroupService"""

    @pytest.mark.asyncio
    async def test_create_group_success(
        self,
        mock_repo,
        mock_credential,
        sample_group_create_dto,
        sample_group_info
    ):
        """Test successful group creation"""
        # Arrange
        service = GroupService(repo=mock_repo)
        
        # Mock the transaction wrapper to execute the function
        async def mock_transaction(func):
            mock_session = AsyncMock()
            return await func(mock_session)
        
        mock_repo.transaction_wrapper = mock_transaction
        
        # Mock get_group to return None (no duplicate)
        mock_group_repo = MagicMock()
        mock_group_repo.get_group = AsyncMock(return_value=None)
        mock_group_repo.create_group = AsyncMock(return_value=sample_group_info)
        mock_repo.group_repo.return_value = mock_group_repo

        # Act
        from app.common.context import AppContext
        from app.common.enum.context_actions import CREATE_GROUP
        ctx = AppContext(trace_id=uuid4(), action=CREATE_GROUP)
        
        result = await service.create_group(
            group_create=sample_group_create_dto,
            credential=mock_credential,
            ctx=ctx
        )

        # Assert
        assert result == sample_group_info
        mock_group_repo.get_group.assert_called_once()
        mock_group_repo.create_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_group_without_name(
        self,
        mock_repo,
        mock_credential
    ):
        """Test group creation without name raises BadRequestException"""
        # Arrange
        service = GroupService(repo=mock_repo)
        
        async def mock_transaction(func):
            mock_session = AsyncMock()
            return await func(mock_session)
        
        mock_repo.transaction_wrapper = mock_transaction
        
        # Note: Pydantic will catch None at validation level, so we test with empty string
        # or test the service logic directly with a bypassed DTO
        from unittest.mock import Mock
        group_create = Mock()
        group_create.name = None  # Bypass Pydantic validation
        group_create.description = "Test"
        group_create.members = []

        # Act & Assert
        from app.common.context import AppContext
        from app.common.enum.context_actions import CREATE_GROUP
        ctx = AppContext(trace_id=uuid4(), action=CREATE_GROUP)
        
        with pytest.raises(BadRequestException) as exc_info:
            await service.create_group(
                group_create=group_create,
                credential=mock_credential,
                ctx=ctx
            )
        
        assert str(exc_info.value.message) == "Group's name is required"

    @pytest.mark.asyncio
    async def test_create_group_duplicate_name(
        self,
        mock_repo,
        mock_credential,
        sample_group_create_dto,
        sample_group_info
    ):
        """Test group creation with duplicate name raises BadRequestException"""
        # Arrange
        service = GroupService(repo=mock_repo)
        
        async def mock_transaction(func):
            mock_session = AsyncMock()
            return await func(mock_session)
        
        mock_repo.transaction_wrapper = mock_transaction
        
        # Mock get_group to return existing group
        mock_group_repo = MagicMock()
        mock_group_repo.get_group = AsyncMock(return_value=sample_group_info)
        mock_repo.group_repo.return_value = mock_group_repo

        # Act & Assert
        from app.common.context import AppContext
        from app.common.enum.context_actions import CREATE_GROUP
        ctx = AppContext(trace_id=uuid4(), action=CREATE_GROUP)
        
        with pytest.raises(BadRequestException) as exc_info:
            await service.create_group(
                group_create=sample_group_create_dto,
                credential=mock_credential,
                ctx=ctx
            )
        
        assert str(exc_info.value.message) == "Group with that name already exists"
        mock_group_repo.get_group.assert_called_once()
