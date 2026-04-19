from typing import Dict, List
from uuid import UUID
from app.common.context import AppContext
from app.common.enum.user_status import UserStatus
from app.common.exceptions import BadRequestException
from app.common.middleware.logger import Logger
from app.common.schemas.common import HashMapResponse
from app.common.schemas.group import (
    GroupCreateDTO,
    GroupCreateDomain,
    GroupInfo,
    GroupJoinOption,
    GroupQuery,
)
from app.common.schemas.user import Credential, UserUpdate
from app.models.group import Group
from app.models.group_members import GroupMembers
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession

logger = Logger()


class GroupService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

    async def _create_group_members(
        self,
        member_ids: List[UUID],
        group_id: UUID,
        ctx: AppContext,
        session: AsyncSession,
        credential: Credential,
    ) -> None:
        member_ids = dict.fromkeys([*(member_ids or []), credential.id])
        new_group_members = [
            GroupMembers(member_id=member_id, group_id=group_id)
            for member_id in member_ids
        ]

        await self.repo.group_members_repo().create(
            group_members=new_group_members,
            ctx=ctx,
            session=session,
        )

    async def _update_first_login_user(
        self,
        credential: Credential,
        new_group: Group,
        ctx: AppContext,
        session: AsyncSession,
    ) -> None:
        logger.info(msg=f"Credential is pending: {credential.is_pending}", context=ctx)

        if credential.is_pending:
            await self.repo.user_repo().update_user(
                session=session,
                user_id=credential.id,
                user_update=UserUpdate(
                    active_group_id=new_group.id, status=UserStatus.ACTIVE
                ),
                ctx=ctx,
            )

    async def create_group(
        self, group_create: GroupCreateDTO, credential: Credential, ctx: AppContext
    ) -> GroupInfo:
        async def _create_group(session: AsyncSession) -> GroupInfo:
            try:
                if group_create.name is None:
                    logger.error(msg=f"Group's name is required", context=ctx)
                    raise BadRequestException(message="Group's name is required")

                group_same_name = await self.repo.group_repo().get_group(
                    session=session, query=GroupQuery(name=group_create.name), ctx=ctx
                )
                if group_same_name is not None:
                    logger.error(
                        msg=f"Group with name {group_create.name} already exists",
                        context=ctx,
                    )
                    raise BadRequestException(
                        message="Group with that name already exists"
                    )

                group_create_domain = GroupCreateDomain(
                    name=group_create.name,
                    description=group_create.description,
                    owner_id=credential.id,
                )
                new_group = await self.repo.group_repo().create_group(
                    session=session, group_create=group_create_domain, ctx=ctx
                )

                await self._create_group_members(
                    member_ids=group_create.members,
                    group_id=new_group.id,
                    ctx=ctx,
                    session=session,
                    credential=credential,
                )

                logger.info(msg=f"Group created successfully", context=ctx)

                await self._update_first_login_user(
                    credential=credential,
                    new_group=new_group,
                    ctx=ctx,
                    session=session,
                )

                logger.info(msg=f"First login user updated successfully", context=ctx)
                return new_group
            except Exception as e:
                logger.error(msg=f"Create group: Exception: {e}", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_create_group)

    async def list_group_key_value(
        self, ctx: AppContext, credential: Credential
    ) -> List[HashMapResponse]:
        async def _list_group_key_value(session: AsyncSession) -> List[Dict[UUID, str]]:
            try:
                query = GroupQuery(owner_id=credential.id)
                groups = await self.repo.group_repo().list_group_map(
                    session=session, query=query, ctx=ctx
                )
                logger.info(msg=f"Groups: {groups}", context=ctx)
                return [
                    HashMapResponse(key=group["id"], value=group["name"])
                    for group in groups
                ]
            except Exception as e:
                logger.error(
                    msg=f"List group key value service: Exception: {e}", context=ctx
                )
                raise e

        return await self.repo.transaction_wrapper(_list_group_key_value)

    async def get_group(
        self, group_id: UUID, ctx: AppContext, credential: Credential
    ) -> Group:
        async def _get_group(session: AsyncSession) -> GroupInfo:
            try:
                group = await self.repo.group_repo().get_group(
                    session=session,
                    query=GroupQuery(id=group_id),
                    ctx=ctx,
                    options=GroupJoinOption(include_members=True),
                )
                if group is None:
                    logger.error(msg=f"Group with id {group_id} not found", context=ctx)
                    raise BadRequestException(message="Group not found")
                if credential.id not in {member.member_id for member in group.members}:
                    logger.error(msg=f"User is not a member of the group", context=ctx)
                    raise BadRequestException(
                        message="User is not a member of the group"
                    )
                return group
            except Exception as e:
                logger.error(msg=f"Get group service: Exception: {e}", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_get_group)
