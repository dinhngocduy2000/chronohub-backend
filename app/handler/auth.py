from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
from fastapi import Depends, Query, Request, Response
from fastapi.responses import RedirectResponse
from app.common.context import AppContext
from app.common.enum.context_actions import (
    AUTHENTICATE_USER,
    GET_CURRENT_USER_PROFILE,
    GOOGLE_AUTHENTICATE,
    LOGOUT,
    REFRESH_TOKEN,
    REGISTER_USER,
    SWITCH_CURRENT_USER_GROUP,
    TRACK_SESSION,
)
from app.common.exceptions import BadRequestException, UnauthorizedException
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.middleware.logger import Logger
from app.common.schemas.common import BaseResponse
from app.common.schemas.user import (
    Credential,
    GoogleAuthUrlResponse,
    GoogleLoginRequest,
    GoogleLoginResponse,
    RefreshTokenRequest,
    SwitchGroupRequest,
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
        self,
        response: Response,
        login_response: UserLoginResponse,
        is_save_session: Optional[bool] = True,
    ) -> None:
        response.set_cookie(
            key="access_token",
            value=login_response.access_token,
            httponly=True,
            secure=True,  # critical on http
            samesite="lax",
            max_age=login_response.expires_in if is_save_session else None,
        )
        response.set_cookie(
            key="refresh_token",
            value=login_response.refresh_token,
            httponly=True,
            secure=True,  # critical on http
            samesite="lax",
            max_age=(
                settings.REFRESH_TOKEN_EXPIRE_SECONDS if is_save_session else None
            ),
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
        logger.info(
            msg=f"Starting Authenticate User Endpoint: {request.url}; email: {login_request.email}",
            context=ctx,
        )
        login_response = await self.service.login_user(login_request, ctx=ctx)
        logger.info(
            msg=f"Authenticate User Endpoint Finishes {request.url}; email: {login_request.email}",
            context=ctx,
        )
        self._set_cookies_tokens(
            response=response,
            login_response=login_response,
            is_save_session=login_request.is_save_session,
        )

        logger.info(msg=f"User logged in successfully", context=ctx)
        return "Success"

    @exception_handler
    async def get_google_auth_url(
        self,
        response: Response,
        request: Request,
    ) -> GoogleLoginResponse:
        """
        Return the Google OAuth authorization URL. Frontend should redirect the user to this URL.
        The backend sets a state cookie; after Google redirects back to the callback, state is validated.
        """
        ctx = AppContext(trace_id=uuid4(), action=GOOGLE_AUTHENTICATE)
        logger.info(
            msg=f"Starting Get Google Auth URL Endpoint: {request.url};",
            context=ctx,
        )
        url, state = self.service.get_google_auth_url(ctx=ctx)
        response.set_cookie(
            key="google_oauth_state",
            value=state,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=600,
        )
        logger.info(
            msg=f"Get Google Auth URL Endpoint Finishes {request.url};",
            context=ctx,
        )
        return GoogleLoginResponse(
            data=GoogleAuthUrlResponse(url=url),
            message="Success",
            statusCode=200,
        )

    @exception_handler
    async def google_callback(
        self,
        request: Request,
        code: str = Query(..., description="Authorization code from Google"),
        state: str = Query(..., description="State string for CSRF check"),
    ) -> RedirectResponse:
        """
        Google OAuth callback. Exchanges the code for tokens, creates session, redirects to frontend.
        """
        ctx = AppContext(trace_id=uuid4(), action=GOOGLE_AUTHENTICATE)
        logger.info(
            msg=f"Starting Google Callback Endpoint: {request.url};",
            context=ctx,
        )
        state_cookie = request.cookies.get("google_oauth_state")
        login_response = await self.service.login_with_google_callback(
            code=code,
            state=state,
            state_cookie=state_cookie,
            ctx=ctx,
        )
        redirect_url = settings.GOOGLE_FRONTEND_REDIRECT_URI or "http://localhost:3000"
        logger.info(
            msg=f"Google Callback Endpoint Finishes {request.url}; Redirecting to {redirect_url}.",
            context=ctx,
        )
        redir = RedirectResponse(url=redirect_url, status_code=302)
        redir.delete_cookie("google_oauth_state")
        self._set_cookies_tokens(
            response=redir,
            login_response=login_response,
            is_save_session=True,
        )
        logger.info(
            msg="User logged in with Google (callback) successfully", context=ctx
        )
        return redir

    @exception_handler
    async def register_user(
        self, request: Request, user_create: UserCreate
    ) -> UserInfo:
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
        logger.info(
            msg=f"Starting Register User Endpoint: {request.url}; params: ${user_create}",
            context=ctx,
        )
        res = await self.service.create_user(user_create, ctx=ctx)
        logger.info(
            msg=f"Register User Endpoint Finishes {request.url}; params: ${user_create};",
            context=ctx,
        )
        return res

    @exception_handler
    async def refresh_token(
        self,
        request: Request,
        response: Response,
        refresh_token_request: RefreshTokenRequest,
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
            raise BadRequestException("Refresh  token is required")
        logger.info(msg=f"Refresh token found, refreshing token...", context=ctx)
        login_response = await self.service.refresh_token(
            refresh_token=refresh_token, ctx=ctx
        )
        logger.info(
            msg=f"Token refreshed successfully, setting cookies...", context=ctx
        )
        self._set_cookies_tokens(
            response=response,
            login_response=login_response,
            is_save_session=refresh_token_request.is_save_session,
        )
        return "Success"

    @exception_handler
    async def get_current_user_profile(
        self,
        request: Request,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> BaseResponse[UserInfo]:
        ctx = AppContext(trace_id=uuid4(), action=GET_CURRENT_USER_PROFILE)
        """
        Get current user profile based on the user id in the credential

        Args:
            credential: Credential object

        Returns:
            UserInfo: User information
        """
        logger.info(
            msg=f"Starting Get Current User Profile Endpoint: {request.url};",
            context=ctx,
        )
        user_info = await self.service.get_current_user(credential.id, ctx=ctx)
        logger.info(
            msg=f"User profile retrieved successfully, returning user info...",
            context=ctx,
        )
        return BaseResponse(
            data=user_info,
            message="Success",
            statusCode=200,
        )

    @exception_handler
    async def switch_current_user_group(
        self,
        request: Request,
        input: SwitchGroupRequest,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> str:
        ctx = AppContext(
            trace_id=uuid4(), action=SWITCH_CURRENT_USER_GROUP, actor=credential.id
        )
        logger.info(
            msg=f"Starting Switch Current User Group Endpoint: {request.url}; params: ${input}",
            context=ctx,
        )
        await self.service.switch_current_user_group(input, ctx=ctx)
        logger.info(
            msg=f"Switch Current User Group Endpoint Finishes {request.url}; params: ${input};",
            context=ctx,
        )
        return "Success"

    @exception_handler
    async def track_session(
        self, credential: Credential = Depends(AuthMiddleware.auth_middleware)
    ) -> str:
        ctx = AppContext(trace_id=uuid4(), action=TRACK_SESSION, actor=credential.id)
        minutes_until_expiry = (
            credential.exp_time - datetime.now(timezone.utc)
        ).total_seconds() / 60
        logger.info(msg=f"current time: {datetime.now(timezone.utc)}", context=ctx)
        logger.info(msg=f"exp time: {credential.exp_time}", context=ctx)
        logger.info(msg=f"Minutes until expiry: {minutes_until_expiry}", context=ctx)
        if minutes_until_expiry < 15:
            raise UnauthorizedException("Session expired")

        return "Session is still valid"

    async def logout(self, response: Response, request: Request) -> str:
        ctx = AppContext(trace_id=uuid4(), action=LOGOUT)
        await self.service.logout(ctx=ctx, response=response, request=request)
        return "Success"
