from datetime import datetime, timedelta, timezone
from app.common.schemas.user import (
    UserCreate,
    UserInfo,
    UserLogin,
    UserLoginResponse,
    UserQuery,
)
from app.common.exceptions import BadRequestException
from app.models.user import User
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from loguru import logger
from app.core.config import settings
import jwt

salt = bcrypt.gensalt()


class AuthService:
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

    async def create_user(self, user_create: UserCreate) -> UserInfo:
        async def _create_user(session: AsyncSession) -> UserInfo:
            if user_create.email is None:
                raise BadRequestException(message="Email is required")
            if user_create.password is None:
                raise BadRequestException(message="Password is required")
            if user_create.name is None:
                raise BadRequestException(message="Name is required")

            user_with_same_email = await self.repo.user_repo().get(
                session=session, query=UserQuery(email=user_create.email)
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

    async def login_user(self, login_request: UserLogin) -> UserLoginResponse:
        async def _login_user(session: AsyncSession) -> UserLoginResponse:
            user = await self.repo.user_repo().get(
                session=session, query=UserQuery(email=login_request.email)
            )
            if user is None:
                raise BadRequestException(
                    message="The user with this email does not exist"
                )

            check_valid_password = bcrypt.checkpw(
                login_request.password.encode("utf-8"), user.password.encode("utf-8")
            )
            if not check_valid_password:
                raise BadRequestException(message="Invalid password")

            login_response = self._generate_tokens(user)
            return login_response

        return await self.repo.transaction_wrapper(_login_user)

    async def refresh_token(self, refresh_token: str) -> UserLoginResponse:
        async def _refresh_token(session: AsyncSession) -> UserLoginResponse:
            try:
                token = jwt.decode(
                    refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                if token["type"] != "refresh":
                    raise BadRequestException(message="Invalid token type")
                user = await self.repo.user_repo().get(
                    session=session, query=UserQuery(id=token["id"])
                )
                if user is None:
                    raise BadRequestException(message="User not found")
                if token["exp"] < datetime.now(timezone.utc).timestamp():
                    raise BadRequestException(message="Token expired")
                return self._generate_tokens(user)
            except jwt.DecodeError as e:
                raise BadRequestException(message="Invalid refresh token")
            except jwt.ExpiredSignatureError as e:
                raise BadRequestException(message="Token expired")
            except jwt.InvalidTokenError as e:
                raise BadRequestException(message="Invalid refresh token")
            except jwt.InvalidSignatureError as e:
                raise BadRequestException(message="Invalid refresh token")
            except jwt.InvalidAlgorithmError as e:
                raise BadRequestException(message="Invalid refresh token")
            except jwt.InvalidKeyError as e:
                raise BadRequestException(message="Invalid refresh token")

        return await self.repo.transaction_wrapper(_refresh_token)
