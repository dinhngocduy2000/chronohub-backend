from typing import List
from fastapi import APIRouter, status, Query, Path
from app.handler.user import UserHandler
from app.common.schemas.user import UserCreate, UserInfo


class UserRouter:
    router: APIRouter
    handler: UserHandler

    def __init__(self, handler: UserHandler) -> None:
        self.router = APIRouter(
            prefix="/users",
            tags=["Users"]
        )
        self.handler = handler
        
        # POST /users - Create user
        self.router.add_api_route(
            path="",
            endpoint=self.handler.create_user,
            methods=["POST"],
            response_model=UserInfo,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new user",
            description="Create a new user account with email, name, and password. "
                       "Password must be at least 8 characters with uppercase, lowercase, number, and special character.",
            response_description="The created user information",
            responses={
                201: {
                    "description": "User created successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "name": "John Doe",
                                "email": "john@example.com",
                                "status": "active",
                                "created_at": "2026-01-25T10:30:00Z",
                                "updated_at": "2026-01-25T10:30:00Z",
                                "image_url": None
                            }
                        }
                    }
                },
                400: {
                    "description": "Bad request - Invalid input data or email already exists",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": "Email already exists"
                            }
                        }
                    }
                },
                422: {
                    "description": "Validation error",
                    "content": {
                        "application/json": {
                            "example": {
                                "detail": [
                                    {
                                        "loc": ["body", "password"],
                                        "msg": "Password must be at least 8 characters long",
                                        "type": "value_error"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        )
