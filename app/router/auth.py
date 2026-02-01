from fastapi import APIRouter, status

from app.common.schemas.user import UserInfo, UserLoginResponse
from app.handler.auth import AuthHandler


class AuthRouter:
    router: APIRouter
    handler: AuthHandler

    def __init__(self, handler: AuthHandler) -> None:
        self.router = APIRouter(prefix="", tags=["Auth"])
        self.handler = handler

        self.router.add_api_route(
            path="/login",
            endpoint=self.handler.authenticate_user,
            methods=["POST"],
            response_model=str,
            status_code=status.HTTP_200_OK,
            summary="Login a user",
            description="Login a user with email and password. ",
            response_description="The logged in user information",
            responses={
                200: {
                    "description": "User logged in successfully",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Successfully logged in"}
                        }
                    },
                },
                400: {
                    "description": "Bad request - Invalid input data or email already exists",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Email already exists"}
                        }
                    },
                },
            },
        )

        self.router.add_api_route(
            path="/refresh",
            endpoint=self.handler.refresh_token,
            methods=["POST"],
            response_model=str,
            status_code=status.HTTP_200_OK,
            summary="Refresh a token",
            description="Refresh a token. ",
            response_description="The refreshed token information",
            responses={
                200: {
                    "description": "Token refreshed successfully",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Successfully refreshed token"}
                        }
                    },
                },
                400: {
                    "description": "Bad request - Invalid refresh token",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Invalid refresh token"}
                        }
                    },
                },
            },
        )

        # POST /users - Create user
        self.router.add_api_route(
            path="/register",
            endpoint=self.handler.register_user,
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
                                "image_url": None,
                            }
                        }
                    },
                },
                400: {
                    "description": "Bad request - Invalid input data or email already exists",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Email already exists"}
                        }
                    },
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
                                        "type": "value_error",
                                    }
                                ]
                            }
                        }
                    },
                },
            },
        )
