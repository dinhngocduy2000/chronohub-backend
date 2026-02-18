from uuid import uuid4

from fastapi import Depends
from app.common.context import AppContext
from app.common.enum.context_actions import CREATE_EVENT
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.schemas.events import EventCreate, EventDetailInfo
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
