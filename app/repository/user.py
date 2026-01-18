from typing import List
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self) -> None:
        pass

    async def create_user(self, session: AsyncSession) -> None:

        pass

    async def get_list_users(self, session: AsyncSession) -> List[str]:
        pass

    async def update_user(self, session: AsyncSession, user_id: str) -> None:
        pass

    async def delete_user(self, session: AsyncSession, user_id: str) -> None:
        pass

    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> None:
        pass
