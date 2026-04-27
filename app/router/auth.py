from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

from app.common.schemas.common import BaseResponse
from app.common.schemas.user import (
    GoogleLoginResponse,
    UserInfo,
)
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
            path="/google",
            endpoint=self.handler.get_google_auth_url,
            methods=["POST"],
            response_model=GoogleLoginResponse,
            status_code=status.HTTP_200_OK,
            summary="Get Google sign-in URL",
            description="Returns the Google OAuth authorization URL. Frontend should redirect the user to this URL to start sign-in. A state cookie is set for validation at the callback.",
            response_description="Object with url to redirect the user to.",
            responses={
                200: {
                    "description": "Google auth URL",
                    "content": {
                        "application/json": {
                            "example": {
                                "url": "https://accounts.google.com/o/oauth2/v2/auth?..."
                            }
                        }
                    },
                },
                400: {
                    "description": "Google Sign-In not configured",
                },
            },
        )

        self.router.add_api_route(
            path="/google/callback",
            endpoint=self.handler.google_callback,
            methods=["GET"],
            response_class=RedirectResponse,
            status_code=status.HTTP_302_FOUND,
            summary="Google OAuth callback",
            description="Called by Google after user signs in. Exchanges the code for tokens, creates session, redirects to the frontend URL.",
            responses={
                302: {"description": "Redirect to frontend with session cookies set"},
                400: {"description": "Invalid state or token exchange failed"},
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
            response_model=str,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new user",
            description="Create a new user account with email, name, and password. "
            "Password must be at least 8 characters with uppercase, lowercase, number, and special character.",
            response_description="The created user information",
            responses={
                201: {
                    "description": "User created successfully",
                    "content": {"application/json": {"example": "Success"}},
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

        # GET /users/me - Get current user profile
        self.router.add_api_route(
            path="/profile",
            endpoint=self.handler.get_current_user_profile,
            methods=["GET"],
            response_model=BaseResponse[UserInfo],
            status_code=status.HTTP_200_OK,
            summary="Get current user profile",
            description="Get current user profile based on the user id in the credential",
            response_description="The current user profile information",
            responses={
                200: {
                    "description": "User profile retrieved successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "data": {
                                    "id": "550e8400-e29b-41d4-a716-446655440000",
                                    "name": "John Doe",
                                    "email": "john@example.com",
                                    "status": "active",
                                    "created_at": "2026-01-25T10:30:00Z",
                                    "updated_at": "2026-01-25T10:30:00Z",
                                    "image_url": None,
                                    "active_group_id": "550e8400-e29b-41d4-a716-446655440000",
                                },
                                "message": "Success",
                                "statusCode": 200,
                            }
                        }
                    },
                },
            },
        )

        self.router.add_api_route(
            path="/switch",
            endpoint=self.handler.switch_current_user_group,
            methods=["PUT"],
            response_model=str,
            status_code=status.HTTP_200_OK,
            summary="Switch current user group",
            description="Switch current user group based on the group id",
            response_description="The switched group information",
        )

        self.router.add_api_route(
            path="/track",
            endpoint=self.handler.track_session,
            methods=["GET"],
            response_model=str,
            status_code=status.HTTP_200_OK,
            summary="Track session",
            description="Track session based on the credential",
            response_description="The tracked session information",
        )

        self.router.add_api_route(
            path="/logout",
            endpoint=self.handler.logout,
            methods=["POST"],
            response_model=str,
            status_code=status.HTTP_200_OK,
            summary="Logout a user",
            description="Logout a user",
            response_description="The logged out user information",
        )
