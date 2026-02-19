import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import UUID
from app.common.context import AppContext
from app.common.middleware.logger import Logger
from app.common.schemas.user import (
    UserCreate,
    UserInfo,
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

salt = bcrypt.gensalt()
logger = Logger()


class UserService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

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
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        return login_response

    async def create_user(self, user_create: UserCreate, ctx: AppContext) -> UserInfo:
        async def _create_user(session: AsyncSession) -> UserInfo:
            if user_create.email is None:
                raise BadRequestException(message="Email is required")
            if user_create.password is None:
                raise BadRequestException(message="Password is required")
            if user_create.name is None:
                raise BadRequestException(message="Name is required")

            user_with_same_email = await self.repo.user_repo().get(
                session=session, query=UserQuery(email=user_create.email), ctx=ctx
            )

            if user_with_same_email is not None:
                raise BadRequestException(message="Email already exists")

            hash_password = bcrypt.hashpw(
                user_create.password.encode("utf-8"), salt
            ).decode("utf-8")

            user_info = User(
                name=user_create.name,
                password=hash_password,
                email=user_create.email,
            )
            await self.repo.user_repo().create_user(
                session=session, user_info=user_info
            )
            return user_info.view()

        return await self.repo.transaction_wrapper(_create_user)

    async def update_user(
        self, user_update: UserUpdate, user_id: UUID, ctx: AppContext
    ) -> UserInfo:
        async def _update_user(session: AsyncSession) -> UserInfo:
            user = await self.repo.user_repo().get(
                session=session, query=UserQuery(id=user_id), ctx=ctx
            )

            user_with_same_email = None

            if user is None:
                logger.error(msg=f"User with id {user_id} not found", context=ctx)
                raise BadRequestException(message="User not found")

            if user_update.email is not None:
                user_with_same_email = await self.repo.user_repo().get(
                    session=session, query=UserQuery(email=user_update.email), ctx=ctx
                )

            if user_with_same_email is not None and user_with_same_email.id != user_id:
                logger.error(
                    msg=f"User with email {user_update.email} already exists",
                    context=ctx,
                )
                raise BadRequestException(message="User with this email already exists")

            new_user = await self.repo.user_repo().update_user(
                session=session, user_id=user_id, user_update=user_update
            )
            return new_user

        return await self.repo.transaction_wrapper(_update_user)

    async def get_user_by_email(self, email: str, ctx: AppContext) -> UserInfo:
        async def _get_user_by_email(session: AsyncSession) -> UserInfo:
            user = await self.repo.user_repo().get(
                session=session, query=UserQuery(email=email), ctx=ctx
            )

            return user.view() if user else None

        return await self.repo.transaction_wrapper(_get_user_by_email)
