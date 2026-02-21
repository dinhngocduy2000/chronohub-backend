from typing import List
from uuid import uuid4

from fastapi import Depends, Query
from app.common.context import AppContext
from app.common.enum.context_actions import CREATE_EVENT, LIST_CALENDAR_EVENTS
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.events import (
    EventCalendarView,
    EventCreate,
    EventDetailInfo,
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
