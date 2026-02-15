from uuid import uuid4
from fastapi import Depends
from app.common.context import AppContext
from app.common.enum.context_actions import CREATE_GROUP
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.group import GroupCreateDTO, GroupInfo
from app.common.schemas.user import Credential
from app.services.group import GroupService


class GroupHandler:
    service: GroupService

    def __init__(self, service: GroupService) -> None:
        self.service = service

    @exception_handler
    async def create_group(
        self,
        group_create: GroupCreateDTO,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> GroupInfo:
        """
        Create a new group

        Args:
            group_create: Group creation data including name, description, and members

        Returns:
            GroupInfo: Created group information
        """
        ctx = AppContext(trace_id=uuid4(), action=CREATE_GROUP)
        return await self.service.create_group(
            group_create, credential=credential, ctx=ctx
        )
