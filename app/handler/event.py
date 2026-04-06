from typing import List
from uuid import UUID, uuid4

from fastapi import Body, Depends, Path, Query, Request
from app.common.context import AppContext
from app.common.enum.context_actions import (
    CREATE_EVENT,
    DELETE_EVENT,
    GET_EVENT_DETAIL,
    LIST_CALENDAR_EVENTS,
    UPDATE_EVENT,
)
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.middleware.logger import Logger
from app.common.schemas.common import BaseResponse
from app.common.schemas.events import (
    EventCalendarView,
    EventCreate,
    EventDetailInfo,
    EventQuery,
    EventUpdate,
    ListEventQuery,
)
from app.common.schemas.user import Credential
from app.services.events import EventService

logger = Logger()


class EventHandler:
    service: EventService

    def __init__(self, service: EventService) -> None:
        self.service = service

    @exception_handler
    async def create_event(
        self,
        event_create: EventCreate,
        request: Request,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> EventDetailInfo:
        ctx = AppContext(trace_id=uuid4(), action=CREATE_EVENT, actor=credential.id)
        logger.info(
            msg=f"Starting Create Event Endpoint: {request.url}; params: ${event_create}",
            context=ctx,
        )
        res = await self.service.create_event(event_create, ctx=ctx)
        logger.info(
            msg=f"Create Event Endpoint Finishes {request.url}; params: ${event_create};",
            context=ctx,
        )
        return res

    @exception_handler
    async def list_calendar_events(
        self,
        request: Request,
        query: ListEventQuery = Query(),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> BaseResponse[List[EventCalendarView]]:
        ctx = AppContext(
            trace_id=uuid4(), action=LIST_CALENDAR_EVENTS, actor=credential.id
        )
        logger.info(
            msg=f"Starting List Calendar Events Endpoint: {request.url}; params: ${query}",
            context=ctx,
        )
        res = await self.service.list_calendar_events(query, ctx=ctx)
        logger.info(
            msg=f"List Calendar Events Endpoint Finishes {request.url}; params: ${query};",
            context=ctx,
        )
        return BaseResponse(
            data=res,
            message="Success",
            statusCode=200,
        )

    @exception_handler
    async def get_event_detail(
        self,
        request: Request,
        id: UUID = Path(..., description="Event id"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> BaseResponse[EventDetailInfo]:
        ctx = AppContext(trace_id=uuid4(), action=GET_EVENT_DETAIL, actor=credential.id)
        query: EventQuery = EventQuery(id=id)
        logger.info(
            msg=f"Starting Get Event Detail Endpoint: {request.url}; params: ${query}",
            context=ctx,
        )
        res = await self.service.get_event_detail(query, ctx=ctx)
        logger.info(
            msg=f"Get Event Detail Endpoint Finishes {request.url}; params: ${query};",
            context=ctx,
        )
        return BaseResponse(
            data=res,
            message="Success",
            statusCode=200,
        )

    @exception_handler
    async def delete_event(
        self,
        request: Request,
        id: UUID = Path(..., description="Event id"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> None:
        ctx = AppContext(trace_id=uuid4(), action=DELETE_EVENT, actor=credential.id)
        logger.info(
            msg=f"Starting Delete Event Endpoint: {request.url}; params: ${id}",
            context=ctx,
        )
        res = await self.service.delete_event(event_id=id, ctx=ctx)
        logger.info(
            msg=f"Delete Event Endpoint Finishes {request.url}; params: ${id};",
            context=ctx,
        )
        return res

    @exception_handler
    async def update_event(
        self,
        request: Request,
        id: UUID = Path(..., description="Event id"),
        event_update: EventUpdate = Body(..., description="Event update"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> str:
        ctx = AppContext(trace_id=uuid4(), action=UPDATE_EVENT, actor=credential.id)
        logger.info(
            msg=f"Starting Update Event Endpoint: {request.url}; params: ${id}",
            context=ctx,
        )
        await self.service.update_event(input=event_update, event_id=id, ctx=ctx)
        logger.info(
            msg=f"Update Event Endpoint Finishes {request.url}; params: ${id};",
            context=ctx,
        )
        return "Success"
