from typing import Dict, List
from uuid import UUID, uuid4
from fastapi import Depends, Path
from app.common.context import AppContext
from app.common.enum.context_actions import (
    CREATE_GROUP,
    GET_GROUP_BY_ID,
    LIST_GROUP_KEY_VALUE,
)
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.common import BaseResponse, HashMapResponse
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

    @exception_handler
    async def list_group_key_value(
        self,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> BaseResponse[List[HashMapResponse]]:
        """
        List all groups with their IDs and names

        Returns:
            List[Dict[UUID, str]]: List of groups with their IDs and names
        """
        ctx = AppContext(trace_id=uuid4(), action=LIST_GROUP_KEY_VALUE)
        groups = await self.service.list_group_key_value(ctx=ctx, credential=credential)
        return BaseResponse(
            data=groups,
            message="Success",
            statusCode=200,
        )

    @exception_handler
    async def get_group(
        self,
        group_id: UUID = Path(..., description="Group id"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> BaseResponse[GroupInfo]:
        """
        Get a group by its ID
        """
        ctx = AppContext(trace_id=uuid4(), action=GET_GROUP_BY_ID, actor=credential.id)
        group = await self.service.get_group(
            group_id=group_id, ctx=ctx, credential=credential
        )
        return BaseResponse(
            data=group.view(),
            message="Success",
            statusCode=200,
        )
