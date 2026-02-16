"""
Integration tests for Group endpoints

These tests use FastAPI's TestClient to test the full endpoint flow.
Authentication is mocked via dependency override in the test_app fixture.
"""
import pytest
from uuid import uuid4

from app.common.exceptions import BadRequestException


class TestGroupEndpoints:
    """Integration tests for group endpoints"""

    def test_create_group_endpoint_success(
        self, 
        test_client,
        mock_group_service,
        sample_group_info
    ):
        """Test POST /create endpoint with valid data"""
        # Arrange
        request_data = {
            "name": "Test Group",
            "description": "Test Description",
            "members": []
        }
        
        # Mock the service to return the group info
        mock_group_service.create_group.return_value = sample_group_info
        
        # Act (authentication is already mocked via test_app fixture)
        response = test_client.post(
            "/api/v1/groups/create",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Group"
        assert "id" in data
        assert "members" in data
        mock_group_service.create_group.assert_called_once()

    def test_create_group_endpoint_missing_name_returns_bad_request(
        self,
        test_client,
        mock_group_service
    ):
        """
        Test POST /create endpoint with missing name
        
        Note: The GroupCreateDTO schema allows name=None (has default),
        so Pydantic validation passes. The service layer validates and
        returns 400 Bad Request.
        """
        # Arrange
        request_data = {
            "description": "Test Description",
            "members": []
        }
        
        # Mock service to raise BadRequestException (as it does in reality)
        mock_group_service.create_group.side_effect = BadRequestException(
            message="Group's name is required"
        )
        
        # Act
        response = test_client.post(
            "/api/v1/groups/create",
            json=request_data
        )
        
        # Assert
        # Service validates and returns 400 (not Pydantic 422)
        assert response.status_code == 400
        data = response.json()
        assert "name is required" in str(data)

    def test_create_group_endpoint_invalid_json(self, test_client):
        """Test POST /create endpoint with invalid JSON"""
        # Act
        response = test_client.post(
            "/api/v1/groups/create",
            data="invalid json"
        )
        
        # Assert
        assert response.status_code == 422

    def test_create_group_endpoint_service_error(
        self, 
        test_client,
        mock_group_service
    ):
        """Test POST /create endpoint when service raises BadRequestException"""
        # Arrange
        request_data = {
            "name": "Existing Group",
            "description": "Test Description",
            "members": []
        }
        
        # Mock the service to raise BadRequestException
        mock_group_service.create_group.side_effect = BadRequestException(
            message="Group with that name already exists"
        )
        
        # Act
        response = test_client.post(
            "/api/v1/groups/create",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Group with that name already exists" in str(data)

    def test_create_group_endpoint_empty_body(self, test_client):
        """Test POST /create endpoint with empty request body"""
        # Act
        response = test_client.post("/api/v1/groups/create")
        
        # Assert
        assert response.status_code == 422

    def test_create_group_endpoint_with_members(
        self,
        test_client,
        mock_group_service,
        sample_group_info
    ):
        """Test POST /create endpoint with members list"""
        # Arrange
        member_ids = [str(uuid4()), str(uuid4())]
        request_data = {
            "name": "Test Group",
            "description": "Test Description",
            "members": member_ids
        }
        
        mock_group_service.create_group.return_value = sample_group_info
        
        # Act
        response = test_client.post(
            "/api/v1/groups/create",
            json=request_data
        )
        
        # Assert
        assert response.status_code == 201
        mock_group_service.create_group.assert_called_once()
