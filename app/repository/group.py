from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import Select, select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.context import AppContext
from app.common.middleware.logger import Logger
from app.common.schemas.group import (
    GroupCreateDomain,
    GroupInfo,
    GroupJoinOption,
    GroupQuery,
    GroupUpdate,
)
from app.models.group import Group
from app.models.group_members import GroupMembers

logger = Logger()


class GroupRepository:

    def __init__(self) -> None:
        pass

    def _prepare_query(
        self, query: GroupQuery, stmt: Select, options: Optional[GroupJoinOption] = None
    ) -> Select:
        if query.id is not None:
            stmt = stmt.where(Group.id == query.id)
        if query.name is not None:
            stmt = stmt.where(Group.name == query.name)
        if query.owner_id is not None:
            stmt = stmt.where(Group.owner_id == query.owner_id)
        if options is not None:
            if options.include_members:
                stmt = stmt.options(
                    joinedload(Group.members).joinedload(GroupMembers.user)
                )
        return stmt

    async def create_group(
        self, session: AsyncSession, group_create: GroupCreateDomain, ctx: AppContext
    ) -> GroupInfo:
        try:
            new_group = Group()
            new_group.name = group_create.name
            new_group.description = group_create.description
            new_group.owner_id = group_create.owner_id
            session.add(new_group)
            await session.flush()
            return new_group.view()
        except Exception as e:
            logger.error(msg=f"Create group repository: Exception: {e}", context=ctx)
            raise e

    async def get_group(
        self,
        session: AsyncSession,
        query: GroupQuery,
        ctx: AppContext,
        options: Optional[GroupJoinOption] = None,
    ) -> Optional[Group]:

        try:
            stmt = select(Group)
            stmt = self._prepare_query(query, stmt, options)
            result = await session.execute(stmt)
            group = result.unique().scalar_one_or_none()
            return group if group else None
        except Exception as e:
            logger.error(msg=f"Get group repository: Exception: {e}", context=ctx)
            raise e

    async def list_groups(
        self, session: AsyncSession, query: GroupQuery, ctx: AppContext
    ) -> List[Group]:
        try:
            stmt = select(Group)
            stmt = self._prepare_query(query, stmt)
            result = await session.execute(stmt)
            groups = result.scalars().all()
            return groups
        except Exception as e:
            logger.error(msg=f"List groups repository: Exception: {e}", context=ctx)
            raise e

    async def list_group_map(
        self, session: AsyncSession, query: GroupQuery, ctx: AppContext
    ) -> List[Dict[UUID, str]]:
        try:
            stmt = select(Group.id, Group.name)
            stmt = self._prepare_query(query, stmt)
            result = await session.execute(stmt)
            groups = result.all()
            return [{"id": group[0], "name": group[1]} for group in groups]
        except Exception as e:
            logger.error(msg=f"List groups repository: Exception: {e}", context=ctx)
            raise e

    async def update_group(
        self, session: AsyncSession, group_update: GroupUpdate, ctx: AppContext
    ) -> GroupInfo:
        try:
            stmt = update(Group).where(Group.id == group_update.id)
            stmt = stmt.values(
                group_update.model_dump(mode="python", exclude_none=True)
            )
            await session.execute(stmt)
            await session.flush()
            return group_update.view()
        except Exception as e:
            logger.error(msg=f"Update group repository: Exception: {e}", context=ctx)
            raise e
