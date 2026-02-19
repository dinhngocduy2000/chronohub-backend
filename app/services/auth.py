import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID
from app.common.context import AppContext
from app.common.enum.user_status import UserStatus
from app.common.middleware.logger import Logger
from app.common.schemas.group import GroupCreateDomain
from app.common.schemas.user import (
    Credential,
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
