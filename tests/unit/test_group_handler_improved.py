"""
Improved unit tests for GroupHandler demonstrating best practices

This file shows advanced testing strategies:
- Comprehensive edge case coverage
- Parameterized tests
- Clear test organization
- Proper error testing
- Mock verification patterns
"""
import pytest
from unittest.mock import AsyncMock, patch, ANY
from uuid import uuid4

from app.handler.group import GroupHandler
from app.common.schemas.group import GroupCreateDTO
from app.common.exceptions import BadRequestException


class TestGroupHandlerCreation:
    """Tests for group creation functionality"""
    
    # ========== SUCCESS SCENARIOS ==========
    
    @pytest.mark.asyncio
    async def test_create_group_with_valid_data_returns_group_info(
        self,
        mock_group_service,
        sample_group_create_dto,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a valid group creation request
        WHEN create_group is called
        THEN it should return the created group information
        """
        # Arrange
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        result = await handler.create_group(
            group_create=sample_group_create_dto,
            credential=mock_credential
        )

        # Assert
        assert result == sample_group_info, "Should return the created group"
        assert result.name == "Test Group", "Group name should match input"
        assert result.id is not None, "Created group should have an ID"
    
    @pytest.mark.asyncio
    async def test_create_group_calls_service_with_correct_parameters(
        self,
        mock_group_service,
        sample_group_create_dto,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a group creation request
        WHEN create_group is called
        THEN the service should be called with correct parameters
        """
        # Arrange
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        await handler.create_group(
            group_create=sample_group_create_dto,
            credential=mock_credential
        )

        # Assert
        mock_group_service.create_group.assert_called_once()
        call_args = mock_group_service.create_group.call_args
        
        # Verify the group_create parameter
        assert call_args.args[0] == sample_group_create_dto
        
        # Verify credential is passed
        assert call_args.kwargs['credential'] == mock_credential
        
        # Verify context is created (we don't care about exact value)
        assert 'ctx' in call_args.kwargs
        assert call_args.kwargs['ctx'] is not None
    
    @pytest.mark.asyncio
    async def test_create_group_with_description_preserves_description(
        self,
        mock_group_service,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a group creation request with description
        WHEN create_group is called
        THEN the description should be preserved in the result
        """
        # Arrange
        group_with_description = GroupCreateDTO(
            name="Group with Description",
            description="This is a detailed description"
        )
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        await handler.create_group(
            group_create=group_with_description,
            credential=mock_credential
        )

        # Assert
        call_args = mock_group_service.create_group.call_args
        assert call_args.args[0].description == "This is a detailed description"
    
    # ========== ERROR SCENARIOS ==========
    
    @pytest.mark.asyncio
    async def test_create_group_when_service_raises_bad_request_propagates_exception(
        self,
        mock_group_service,
        sample_group_create_dto,
        mock_credential
    ):
        """
        GIVEN the service raises BadRequestException
        WHEN create_group is called
        THEN the exception should propagate to the caller
        """
        # Arrange
        expected_error = BadRequestException(message="Group name already exists")
        mock_group_service.create_group.side_effect = expected_error
        handler = GroupHandler(service=mock_group_service)

        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            await handler.create_group(
                group_create=sample_group_create_dto,
                credential=mock_credential
            )
        
        assert str(exc_info.value.message) == "Group name already exists"
        mock_group_service.create_group.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_when_service_raises_generic_exception_wraps_in_internal_error(
        self,
        mock_group_service,
        sample_group_create_dto,
        mock_credential
    ):
        """
        GIVEN the service raises a generic exception
        WHEN create_group is called
        THEN it should be wrapped in ExceptionInternalError by the decorator
        """
        # Arrange
        from app.common.exceptions import ExceptionInternalError
        mock_group_service.create_group.side_effect = Exception("Database connection failed")
        handler = GroupHandler(service=mock_group_service)

        # Act & Assert
        # The @exception_handler decorator wraps generic exceptions
        with pytest.raises(ExceptionInternalError) as exc_info:
            await handler.create_group(
                group_create=sample_group_create_dto,
                credential=mock_credential
            )
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"
        mock_group_service.create_group.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("error_message", [
        "Database error",
        "Connection timeout",
        "Internal server error",
        "Unexpected error occurred",
    ])
    async def test_create_group_with_various_errors_wraps_in_internal_error(
        self,
        mock_group_service,
        sample_group_create_dto,
        mock_credential,
        error_message
    ):
        """
        GIVEN various error scenarios in the service
        WHEN create_group is called
        THEN all should be wrapped in ExceptionInternalError
        """
        # Arrange
        from app.common.exceptions import ExceptionInternalError
        mock_group_service.create_group.side_effect = Exception(error_message)
        handler = GroupHandler(service=mock_group_service)

        # Act & Assert
        # The @exception_handler decorator normalizes all generic exceptions
        with pytest.raises(ExceptionInternalError) as exc_info:
            await handler.create_group(
                group_create=sample_group_create_dto,
                credential=mock_credential
            )
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"
    
    # ========== EDGE CASES ==========
    
    @pytest.mark.asyncio
    async def test_create_group_with_empty_members_list_succeeds(
        self,
        mock_group_service,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a group creation request with empty members list
        WHEN create_group is called
        THEN it should succeed
        """
        # Arrange
        group_no_members = GroupCreateDTO(
            name="Solo Group",
            description="No members",
            members=[]
        )
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        result = await handler.create_group(
            group_create=group_no_members,
            credential=mock_credential
        )

        # Assert
        assert result is not None
        mock_group_service.create_group.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_group_with_multiple_members_passes_all_members(
        self,
        mock_group_service,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a group creation request with multiple members
        WHEN create_group is called
        THEN all member IDs should be passed to the service
        """
        # Arrange
        member_ids = [uuid4(), uuid4(), uuid4()]
        group_with_members = GroupCreateDTO(
            name="Team Group",
            description="With members",
            members=member_ids
        )
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        await handler.create_group(
            group_create=group_with_members,
            credential=mock_credential
        )

        # Assert
        call_args = mock_group_service.create_group.call_args
        passed_group = call_args.args[0]
        assert len(passed_group.members) == 3
        assert all(member_id in passed_group.members for member_id in member_ids)
    
    # ========== CONTEXT VERIFICATION ==========
    
    @pytest.mark.asyncio
    async def test_create_group_generates_unique_trace_id_in_context(
        self,
        mock_group_service,
        sample_group_create_dto,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN multiple group creation requests
        WHEN create_group is called multiple times
        THEN each call should have a unique trace_id
        """
        # Arrange
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        await handler.create_group(sample_group_create_dto, mock_credential)
        first_call_ctx = mock_group_service.create_group.call_args.kwargs['ctx']
        
        await handler.create_group(sample_group_create_dto, mock_credential)
        second_call_ctx = mock_group_service.create_group.call_args.kwargs['ctx']

        # Assert
        assert first_call_ctx.trace_id != second_call_ctx.trace_id, \
            "Each request should have a unique trace_id"
    
    @pytest.mark.asyncio
    async def test_create_group_context_has_correct_action(
        self,
        mock_group_service,
        sample_group_create_dto,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a group creation request
        WHEN create_group is called
        THEN the context should have CREATE_GROUP action
        """
        # Arrange
        from app.common.enum.context_actions import CREATE_GROUP
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        await handler.create_group(
            group_create=sample_group_create_dto,
            credential=mock_credential
        )

        # Assert
        call_args = mock_group_service.create_group.call_args
        context = call_args.kwargs['ctx']
        assert context.action == CREATE_GROUP


class TestGroupHandlerIntegration:
    """Integration-style tests for handler behavior"""
    
    @pytest.mark.asyncio
    async def test_handler_maintains_service_contract(
        self,
        mock_group_service,
        sample_group_create_dto,
        sample_group_info,
        mock_credential
    ):
        """
        GIVEN a properly initialized handler
        WHEN any valid operation is performed
        THEN it should maintain the service contract
        """
        # Arrange
        mock_group_service.create_group.return_value = sample_group_info
        handler = GroupHandler(service=mock_group_service)

        # Act
        result = await handler.create_group(
            group_create=sample_group_create_dto,
            credential=mock_credential
        )

        # Assert - Verify service contract
        assert result is not None, "Handler should return non-null result"
        assert hasattr(result, 'id'), "Result should have id field"
        assert hasattr(result, 'name'), "Result should have name field"
        assert hasattr(result, 'created_at'), "Result should have created_at field"
        assert hasattr(result, 'updated_at'), "Result should have updated_at field"
        assert hasattr(result, 'members'), "Result should have members field"


class TestGroupHandlerErrorRecovery:
    """Tests for error handling and recovery scenarios"""
    
    @pytest.mark.asyncio
    async def test_handler_wraps_runtime_errors_in_internal_error(
        self,
        mock_group_service,
        sample_group_create_dto,
        mock_credential
    ):
        """
        GIVEN the service raises a RuntimeError
        WHEN create_group is called
        THEN the handler should wrap it in ExceptionInternalError
        """
        # Arrange
        from app.common.exceptions import ExceptionInternalError
        mock_group_service.create_group.side_effect = RuntimeError("Critical error")
        handler = GroupHandler(service=mock_group_service)

        # Act & Assert
        # The @exception_handler decorator wraps RuntimeError in ExceptionInternalError
        with pytest.raises(ExceptionInternalError) as exc_info:
            await handler.create_group(
                group_create=sample_group_create_dto,
                credential=mock_credential
            )
        
        assert exc_info.value.status_code == 500
