from app.common.schemas.user import UserCreate, UserInfo
from app.common.exceptions import BadRequestException
from app.models.user import User
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt

salt = bcrypt.gensalt()


class UserService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

    async def create_user(self, user_create: UserCreate) -> UserInfo:
        async def _create_user(session: AsyncSession) -> UserInfo:
            if user_create.email is None:
                raise BadRequestException(message="Email is required")
            if user_create.password is None:
                raise BadRequestException(message="Password is required")
            if user_create.name is None:
                raise BadRequestException(message="Name is required")

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
