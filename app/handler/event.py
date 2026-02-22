from typing import List
from uuid import UUID, uuid4

from fastapi import Body, Depends, Path, Query
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


class EventHandler:
    service: EventService

    def __init__(self, service: EventService) -> None:
        self.service = service

    @exception_handler
    async def create_event(
        self,
        event_create: EventCreate,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> EventDetailInfo:
        ctx = AppContext(trace_id=uuid4(), action=CREATE_EVENT, actor=credential.id)
        return await self.service.create_event(event_create, ctx=ctx)

    @exception_handler
    async def list_calendar_events(
        self,
        query: ListEventQuery = Query(),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> List[EventCalendarView]:
        ctx = AppContext(
            trace_id=uuid4(), action=LIST_CALENDAR_EVENTS, actor=credential.id
        )
        return await self.service.list_calendar_events(query, ctx=ctx)

    @exception_handler
    async def get_event_detail(
        self,
        id: UUID = Path(..., description="Event id"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> EventDetailInfo:
        ctx = AppContext(trace_id=uuid4(), action=GET_EVENT_DETAIL, actor=credential.id)
        query: EventQuery = EventQuery(id=id)
        return await self.service.get_event_detail(query, ctx=ctx)

    @exception_handler
    async def delete_event(
        self,
        id: UUID = Path(..., description="Event id"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> None:
        ctx = AppContext(trace_id=uuid4(), action=DELETE_EVENT, actor=credential.id)
        return await self.service.delete_event(event_id=id, ctx=ctx)

    @exception_handler
    async def update_event(
        self,
        id: UUID = Path(..., description="Event id"),
        event_update: EventUpdate = Body(..., description="Event update"),
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> str:
        ctx = AppContext(trace_id=uuid4(), action=UPDATE_EVENT, actor=credential.id)
        await self.service.update_event(input=event_update, event_id=id, ctx=ctx)
        return "Success"
