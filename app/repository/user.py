from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.user import UserInfo
from app.models.user import User


class UserRepository:
    def __init__(self) -> None:
        pass

    async def create_user(self, session: AsyncSession, user_info: User) -> UserInfo:
        session.add(user_info)  # Note: session.add() is NOT async, no await needed
        await session.flush()  # Flush to get the ID if needed
        return user_info.view()

    async def get_list_users(self, session: AsyncSession) -> List[str]:
        pass

    async def update_user(self, session: AsyncSession, user_id: str) -> None:
        pass

    async def delete_user(self, session: AsyncSession, user_id: str) -> None:
        pass

    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> None:
        pass
