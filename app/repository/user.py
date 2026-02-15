from typing import List, Optional
from sqlalchemy import UUID, Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enum.user_status import UserStatus
from app.common.schemas.user import UserInfo, UserQuery, UserUpdate
from app.models.user import User


class UserRepository:
    def __init__(self) -> None:
        pass

    def _prepare_query(self, query: UserQuery, stmt: Select) -> Select:
        stmt = stmt.where(User.status != UserStatus.DELETED)

        if query.id is not None:
            stmt = stmt.where(User.id == query.id)
        if query.email is not None:
            stmt = stmt.where(User.email == query.email)
        if query.name is not None:
            stmt = stmt.where(User.name == query.name)
        if query.status is not None:
            stmt = stmt.where(User.status == query.status)

        return stmt

    async def create_user(self, session: AsyncSession, user_info: User) -> UserInfo:
        session.add(user_info)  # Note: session.add() is NOT async, no await needed
        await session.flush()  # Flush to get the ID if needed
        return user_info.view()

    async def get_list_users(self, session: AsyncSession) -> List[str]:
        pass

    async def update_user(
        self, session: AsyncSession, user_id: UUID, user_update: UserUpdate
    ) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                name=user_update.name,
                email=user_update.email,
                password=user_update.password,
                image_url=user_update.image_url,
                status=user_update.status,
                updated_at=func.now(),
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def delete_user(self, session: AsyncSession, user_id: str) -> None:
        pass

    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> None:
        pass

    async def get(self, session: AsyncSession, query: UserQuery) -> Optional[User]:
        stmt = select(User)
        stmt = self._prepare_query(query, stmt)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user if user else None
