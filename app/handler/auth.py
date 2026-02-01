from uuid import uuid4
from fastapi import Depends, Request, Response
from app.common.context import AppContext
from app.common.enum.context_actions import (
    AUTHENTICATE_USER,
    GET_CURRENT_USER_PROFILE,
    REFRESH_TOKEN,
    REGISTER_USER,
)
from app.common.exceptions import BadRequestException
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.middleware.logger import Logger
from app.common.schemas.user import (
    Credential,
    RefreshTokenRequest,
    UserCreate,
    UserInfo,
    UserLogin,
    UserLoginResponse,
)
from app.services.auth import AuthService
from app.core.config import settings

logger = Logger()


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
        ctx = AppContext(trace_id=uuid4(), action=AUTHENTICATE_USER)

        login_response = await self.service.login_user(login_request, ctx=ctx)

        self._set_cookies_tokens(response=response, login_response=login_response)
        logger.info(msg=f"User logged in successfully", context=ctx)
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
        ctx = AppContext(trace_id=uuid4(), action=REGISTER_USER)
        return await self.service.create_user(user_create, ctx=ctx)

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
        ctx = AppContext(trace_id=uuid4(), action=REFRESH_TOKEN)
        logger.info(msg=f"Getting refresh token from cookies...", context=ctx)
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token is None:
            logger.error(msg=f"Refresh token not found in cookies...", context=ctx)
            raise BadRequestException("Refresh token is required")
        logger.info(msg=f"Refresh token found, refreshing token...", context=ctx)
        login_response = await self.service.refresh_token(
            refresh_token=refresh_token, ctx=ctx
        )
        logger.info(
            msg=f"Token refreshed successfully, setting cookies...", context=ctx
        )
        self._set_cookies_tokens(response=response, login_response=login_response)
        return "Success"

    @exception_handler
    async def get_current_user_profile(
        self, credential: Credential = Depends(AuthMiddleware.auth_middleware)
    ) -> UserInfo:
        ctx = AppContext(trace_id=uuid4(), action=GET_CURRENT_USER_PROFILE)
        """
        Get current user profile based on the user id in the credential

        Args:
            credential: Credential object

        Returns:
            UserInfo: User information
        """
        user_info = await self.service.get_current_user(credential.id, ctx=ctx)
        logger.info(
            msg=f"User profile retrieved successfully, returning user info...",
            context=ctx,
        )
        logger.info(msg=f"User info: {user_info}", context=ctx)
        return user_info
