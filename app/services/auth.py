import asyncio
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Tuple
from uuid import UUID

import httpx
from fastapi import Response
from app.common.context import AppContext
from app.common.enum.user_status import UserStatus
from app.common.middleware.logger import Logger
from app.common.schemas.group import GroupCreateDomain, GroupQuery
from app.common.schemas.user import (
    Credential,
    SwitchGroupRequest,
    UserCreate,
    UserInfo,
    UserJoinOption,
    UserLogin,
    UserLoginResponse,
    UserQuery,
    UserUpdate,
)
from app.common.exceptions import BadRequestException
from app.models.user import User
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from app.core.config import settings
import jwt
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.services.group import GroupService
from app.services.user import UserService

salt = bcrypt.gensalt()

logger = Logger()


class AuthService:
    repo: Registry
    group_service: GroupService
    user_service: UserService

    def __init__(
        self, repo: Registry, group_service: GroupService, user_service: UserService
    ) -> None:
        self.repo = repo
        self.group_service = group_service
        self.user_service = user_service

    def _generate_tokens(self, user: User) -> UserLoginResponse:
        current_time = datetime.now(timezone.utc)
        jwt_payload = {"iat": current_time, "id": str(user.id), "email": user.email}

        # access token
        jwt_payload["type"] = "access"
        jwt_payload["exp"] = current_time + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        access_token = jwt.encode(
            jwt_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        # refresh token
        jwt_payload["type"] = "refresh"
        jwt_payload["exp"] = current_time + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_token = jwt.encode(
            jwt_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        login_response = UserLoginResponse(
            email=user.email,
            name=user.name,
            status=user.status,
            id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return login_response

    async def create_user(self, user_create: UserCreate, ctx: AppContext) -> UserInfo:
        async def _create_user(session: AsyncSession) -> UserInfo:
            logger.info(msg=f"Checking user creation data...", context=ctx)
            if user_create.email is None:
                logger.error(msg=f"Email is required", context=ctx)
                raise BadRequestException(message="Email is required")
            if user_create.password is None:
                logger.error(msg=f"Password is required", context=ctx)
                raise BadRequestException(message="Password is required")
            if user_create.name is None:
                logger.error(msg=f"Name is required", context=ctx)
                raise BadRequestException(message="Name is required")

            logger.info(
                msg=f"Checking if user with email {user_create.email} already exists...",
                context=ctx,
            )

            user_with_same_email = await self.repo.user_repo().get(
                session=session, query=UserQuery(email=user_create.email), ctx=ctx
            )

            if user_with_same_email is not None:
                logger.error(
                    msg=f"User with email {user_create.email} already exists",
                    context=ctx,
                )
                raise BadRequestException(message="Email already exists")

            logger.info(msg=f"Hashing password...", context=ctx)
            hash_password = bcrypt.hashpw(
                user_create.password.encode("utf-8"), salt
            ).decode("utf-8")

            logger.info(msg=f"Hasing password complete, creating user...", context=ctx)
            user_info = User(
                name=user_create.name,
                password=hash_password,
                email=user_create.email,
            )
            await self.repo.user_repo().create_user(
                session=session, user_info=user_info
            )
            logger.info(
                msg=f"User created successfully, returning user info...", context=ctx
            )
            return user_info.view()

        return await self.repo.transaction_wrapper(_create_user)

    async def login_user(
        self, login_request: UserLogin, ctx: AppContext
    ) -> UserLoginResponse:
        async def _login_user(session: AsyncSession) -> UserLoginResponse:
            try:
                logger.info(
                    msg=f"Checking user email... {login_request.email}", context=ctx
                )
                user = await self.repo.user_repo().get(
                    session=session, query=UserQuery(email=login_request.email), ctx=ctx
                )
                if user is None:
                    logger.error(
                        msg=f"User with email {login_request.email} not found",
                        context=ctx,
                    )
                    raise BadRequestException(
                        message="The user with this email does not exist"
                    )

                logger.info(
                    msg=f"User found with email {login_request.email}", context=ctx
                )

                logger.info(msg=f"Validating password...", context=ctx)

                check_valid_password = bcrypt.checkpw(
                    login_request.password.encode("utf-8"),
                    user.password.encode("utf-8"),
                )
                if not check_valid_password:
                    logger.error(msg=f"Incorrect password", context=ctx)
                    raise BadRequestException(message="Invalid password")

                logger.info(
                    msg=f"Password validated successfully, generating tokens...",
                    context=ctx,
                )

                login_response = self._generate_tokens(user)

                logger.info(
                    msg=f"Tokens generated successfully, settings tokens to cookies...",
                    context=ctx,
                )

                if user.status == UserStatus.PENDING:
                    logger.info(
                        msg=f"User login for first time, creating default group..."
                    )

                    new_group = await self.group_service.create_group(
                        group_create=GroupCreateDomain(
                            name=f"{user.name}'s Group",
                            description=f"Group created for {user.name} by default",
                        ),
                        credential=Credential(
                            id=user.id, email=user.email, is_pending=False
                        ),
                        ctx=ctx,
                    )

                    logger.info(
                        msg=f"Default group created successfully, updating user...",
                        context=ctx,
                    )
                    user_update = UserUpdate(
                        name=user.name,
                        email=user.email,
                        password=user.password,
                        image_url=user.image_url,
                        status=UserStatus.ACTIVE,
                        active_group_id=new_group.id,
                    )
                    asyncio.create_task(
                        self.user_service.update_user(
                            user_update=user_update, user_id=user.id, ctx=ctx
                        ),
                    )

                return login_response
            except Exception as e:
                logger.error(msg=f"Login user failed: Exception", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_login_user)

    def get_google_auth_url(self, ctx: AppContext) -> Tuple[str, str]:
        """
        Build the Google OAuth 2.0 authorization URL for redirect-based sign-in.
        Returns (url, state). The handler should set state in a cookie and return the URL to the frontend.
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
            logger.error(
                msg="Google OAuth URL is not configured (GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI)",
                context=ctx,
            )
            raise BadRequestException(message="Google Sign-In is not configured")
        state = secrets.token_urlsafe(32)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
            params
        )
        return url, state

    async def _login_response_from_google_idinfo(
        self, idinfo: dict, ctx: AppContext
    ) -> UserLoginResponse:
        """Get or create user from Google id_token payload and return our JWT login response."""
        email = idinfo.get("email")
        if not email or not idinfo.get("email_verified"):
            raise BadRequestException(message="Google account email is not verified")
        name = idinfo.get("name") or email.split("@")[0]
        picture = idinfo.get("picture")

        async def _run(session: AsyncSession) -> UserLoginResponse:
            user = await self.repo.user_repo().get(
                session=session,
                query=UserQuery(email=email),
                ctx=ctx,
            )
            if user is None:
                logger.info(
                    msg=f"Creating new user for Google sign-in: {email}",
                    context=ctx,
                )
                new_user = User(
                    name=name,
                    email=email,
                    password=None,
                    image_url=picture,
                )
                await self.repo.user_repo().create_user(
                    session=session,
                    user_info=new_user,
                )
                await session.refresh(new_user)
                user = new_user

            login_response = self._generate_tokens(user)
            if user.status == UserStatus.PENDING:
                logger.info(
                    msg="First-time Google login: creating default group...",
                    context=ctx,
                )
                new_group = await self.group_service.create_group(
                    group_create=GroupCreateDomain(
                        name=f"{user.name}'s Group",
                        description=f"Group created for {user.name} by default",
                    ),
                    credential=Credential(
                        id=user.id,
                        email=user.email,
                        is_pending=False,
                    ),
                    ctx=ctx,
                )
                user_update = UserUpdate(
                    name=user.name,
                    email=user.email,
                    password=user.password,
                    image_url=user.image_url,
                    status=UserStatus.ACTIVE,
                    active_group_id=new_group.id,
                )
                asyncio.create_task(
                    self.user_service.update_user(
                        user_update=user_update,
                        user_id=user.id,
                        ctx=ctx,
                    ),
                )
            return login_response

        return await self.repo.transaction_wrapper(_run)

    async def login_with_google_callback(
        self, code: str, state: str, state_cookie: str | None, ctx: AppContext
    ) -> UserLoginResponse:
        """
        Exchange Google authorization code for tokens, then get or create user and return our JWTs.
        Validates state against the cookie set when the auth URL was requested.
        """
        if not all(
            [
                settings.GOOGLE_CLIENT_ID,
                settings.GOOGLE_CLIENT_SECRET,
                settings.GOOGLE_REDIRECT_URI,
            ]
        ):
            logger.error(
                msg="Google callback is not configured",
                context=ctx,
            )
            raise BadRequestException(message="Google Sign-In is not configured")
        if not state or state != state_cookie:
            logger.error(msg="Invalid or missing state in Google callback", context=ctx)
            raise BadRequestException(message="Invalid state")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            logger.error(
                msg=f"Google token exchange failed: {resp.status_code} {resp.text}",
                context=ctx,
            )
            raise BadRequestException(message="Google sign-in failed")

        data = resp.json()
        id_token_str = data.get("id_token")
        if not id_token_str:
            logger.error(msg="Google response missing id_token", context=ctx)
            raise BadRequestException(message="Google sign-in failed")

        try:
            idinfo = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            logger.error(
                msg=f"Invalid Google ID token from callback: {e}",
                context=ctx,
            )
            raise BadRequestException(message="Invalid Google credential")

        return await self._login_response_from_google_idinfo(idinfo, ctx)

    async def refresh_token(
        self, refresh_token: str, ctx: AppContext
    ) -> UserLoginResponse:
        async def _refresh_token(session: AsyncSession) -> UserLoginResponse:
            logger.info(msg=f"Decoding refresh token...", context=ctx)
            try:
                token = jwt.decode(
                    refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                if token["type"] != "refresh":
                    logger.error(msg=f"Invalid token type", context=ctx)
                    raise BadRequestException(message="Invalid token type")
                user = await self.repo.user_repo().get(
                    session=session, query=UserQuery(id=token["id"]), ctx=ctx
                )
                if user is None:
                    logger.error(
                        msg=f"User with id {token['id']} not found", context=ctx
                    )
                    raise BadRequestException(message="User not found")
                if token["exp"] < datetime.now(timezone.utc).timestamp():
                    logger.error(msg=f"Token expired", context=ctx)
                    raise BadRequestException(message="Token expired")
                logger.info(
                    msg=f"Token decoded successfully, generating new tokens...",
                    context=ctx,
                )
                return self._generate_tokens(user)
            except jwt.DecodeError as e:
                logger.error(msg=f"Invalid refresh token: DecodeError", context=ctx)
                raise BadRequestException(message="Invalid refresh token")
            except jwt.ExpiredSignatureError as e:
                logger.error(
                    msg=f"Invalid refresh token: ExpiredSignatureError", context=ctx
                )
                raise BadRequestException(message="Token expired")
            except jwt.InvalidTokenError as e:
                logger.error(
                    msg=f"Invalid refresh token: InvalidTokenError", context=ctx
                )
                raise BadRequestException(message="Invalid refresh token")
            except jwt.InvalidSignatureError as e:
                logger.error(
                    msg=f"Invalid refresh token: InvalidSignatureError", context=ctx
                )
                raise BadRequestException(message="Invalid refresh token")
            except jwt.InvalidAlgorithmError as e:
                logger.error(
                    msg=f"Invalid refresh token: InvalidAlgorithmError", context=ctx
                )
                raise BadRequestException(message="Invalid refresh token")
            except jwt.InvalidKeyError as e:
                logger.error(msg=f"Invalid refresh token: InvalidKeyError", context=ctx)
                raise BadRequestException(message="Invalid refresh token")
            except Exception as e:
                logger.error(msg=f"Invalid refresh token: Exception", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_refresh_token)

    async def get_current_user(self, user_id: UUID, ctx: AppContext) -> UserInfo:
        async def _get_current_user(session: AsyncSession) -> UserInfo:
            logger.info(msg=f"Getting user by id {user_id}...", context=ctx)
            user = await self.repo.user_repo().get(
                session=session,
                query=UserQuery(id=user_id),
                ctx=ctx,
                options=UserJoinOption(included_owned_groups=True),
            )
            if user is None:
                logger.error(msg=f"User with id {user_id} not found", context=ctx)
                raise BadRequestException(message="User not found")
            logger.info(
                msg=f"User found with id {user_id}: {user.__dict__}", context=ctx
            )
            user_info_data = user.view().model_dump(
                mode="python", exclude={"owned_groups"}
            )
            return UserInfo(
                **user_info_data,
                owned_groups=[group.view() for group in user.owned_groups],
            )

        return await self.repo.transaction_wrapper(_get_current_user)

    async def switch_current_user_group(
        self, input: SwitchGroupRequest, ctx: AppContext
    ) -> None:
        async def _switch_current_user_group(session: AsyncSession) -> None:
            try:
                user, group = await asyncio.gather(
                    self.repo.user_repo().get(
                        session=session, query=UserQuery(id=ctx.actor), ctx=ctx
                    ),
                    self.repo.group_repo().get_group(
                        session=session, query=GroupQuery(id=input.group_id), ctx=ctx
                    ),
                )
                if user is None:
                    logger.error(msg=f"User with id {ctx.actor} not found", context=ctx)
                    raise BadRequestException(message="User not found")

                if group is None:
                    logger.error(
                        msg=f"Group with id {input.group_id} not found", context=ctx
                    )
                    raise BadRequestException(message="Group not found")

                if user.active_group_id == input.group_id:
                    logger.info(
                        msg=f"User already in group {input.group_id}", context=ctx
                    )
                    return

                await self.repo.user_repo().update_user(
                    session=session,
                    user_id=ctx.actor,
                    user_update=UserUpdate(active_group_id=input.group_id),
                    ctx=ctx,
                )
                return
            except Exception as e:
                logger.error(msg=f"Switch group service: Exception: {e}", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_switch_current_user_group)

    async def logout(self, ctx: AppContext, response: Response) -> None:
        try:
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return
        except Exception as e:
            logger.error(msg=f"Logout service: Exception: {e}", context=ctx)
            raise e
