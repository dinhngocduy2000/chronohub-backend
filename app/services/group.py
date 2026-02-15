from app.common.context import AppContext
from app.common.exceptions import BadRequestException
from app.common.middleware.logger import Logger
from app.common.schemas.group import (
    GroupCreateDTO,
    GroupCreateDomain,
    GroupInfo,
    GroupQuery,
)
from app.common.schemas.user import Credential
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession

logger = Logger()


class GroupService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

    async def create_group(
        self, group_create: GroupCreateDTO, credential: Credential, ctx: AppContext
    ) -> GroupInfo:
        async def _create_group(session: AsyncSession) -> GroupInfo:
            try:
                if group_create.name is None:
                    logger.error(msg=f"Group's name is required", context=ctx)
                    raise BadRequestException(message="Group's name is required")

                group_same_name = await self.repo.group_repo().get_group(
                    session=session, query=GroupQuery(name=group_create.name)
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
                    session=session, group_create=group_create_domain
                )
                logger.info(msg=f"Group created successfully", context=ctx)
                return new_group
            except Exception as e:
                logger.error(msg=f"Create group: Exception: {e}", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_create_group)
