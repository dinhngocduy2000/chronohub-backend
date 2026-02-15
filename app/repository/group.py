from typing import Optional
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.schemas.group import GroupCreateDomain, GroupInfo, GroupQuery
from app.models.group import Group


class GroupRepository:

    def __init__(self) -> None:
        pass

    def _prepare_query(self, query: GroupQuery, stmt: Select) -> Select:
        if query.id is not None:
            stmt = stmt.where(Group.id == query.id)
        if query.name is not None:
            stmt = stmt.where(Group.name == query.name)
        if query.owner_id is not None:
            stmt = stmt.where(Group.owner_id == query.owner_id)
        return stmt

    async def create_group(
        self, session: AsyncSession, group_create: GroupCreateDomain
    ) -> GroupInfo:
        new_group = Group()
        new_group.name = group_create.name
        new_group.description = group_create.description
        new_group.owner_id = group_create.owner_id
        session.add(new_group)
        await session.flush()
        return new_group.view()

    async def get_group(
        self, session: AsyncSession, query: GroupQuery
    ) -> Optional[Group]:

        stmt = select(Group)
        stmt = self._prepare_query(query, stmt)
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()
        return group if group else None
