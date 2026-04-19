from typing import List
from app.common.context import AppContext
from app.common.middleware.logger import Logger
from app.common.schemas.group import GroupMemberInfo
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_members import GroupMembers

logger = Logger()


class GroupMembersRepository:
    def __init__(self) -> None:
        pass

    async def create(
        self, session: AsyncSession, group_members: List[GroupMembers], ctx: AppContext
    ) -> List[GroupMembers]:

        try:
            session.add_all(group_members)
            await session.flush()
            return group_members
        except Exception as e:
            logger.error(
                msg=f"Create group members repository: Exception: {e}", context=ctx
            )
            raise e
