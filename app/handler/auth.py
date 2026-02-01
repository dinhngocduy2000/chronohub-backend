from fastapi import Depends, Request, Response
from app.common.exceptions import BadRequestException
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.user import (
    Credential,
    RefreshTokenRequest,
    UserCreate,
    UserInfo,
    UserLogin,
    UserLoginResponse,
)
from app.services.auth import AuthService
from loguru import logger
from app.core.config import settings


class AuthHandler:
    service: AuthService

    def __init__(self, service: AuthService) -> None:
        self.service = service

    def _set_cookies_tokens(
        self, response: Response, login_response: UserLoginResponse
    ) -> None:
        response.set_cookie(
            key="access_token",
            value=login_response.access_token,
            httponly=True,
            secure=True,
            max_age=login_response.expires_in,
        )
        response.set_cookie(
            key="refresh_token",
            value=login_response.refresh_token,
            httponly=True,
            secure=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    @exception_handler
    async def authenticate_user(
        self, login_request: UserLogin, response: Response, request: Request
    ) -> str:
        """
        Login a user

        Args:
            login_request: User login data including email and password

        Returns:
            str: Success message
        """

        login_response = await self.service.login_user(login_request)
        self._set_cookies_tokens(response=response, login_response=login_response)
        return "Success"

    @exception_handler
    async def register_user(self, user_create: UserCreate) -> UserInfo:
        """
        Create a new user account

        Args:
            user_data: User registration data including email, name, and password

        Returns:
            UserInfo: Created user information

        Raises:
            BadRequestException: If email already exists or validation fails
        """
        return await self.service.create_user(user_create)

    @exception_handler
    async def refresh_token(
        self,
        request: Request,
        response: Response,
    ) -> str:
        """
        Refresh a token

        Args:
            refresh_token: User refresh token

        Returns:
            str: Success message
        """
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token is None:
            raise BadRequestException("Refresh token is required")
        login_response = await self.service.refresh_token(refresh_token)
        self._set_cookies_tokens(response=response, login_response=login_response)
        return "Success"
