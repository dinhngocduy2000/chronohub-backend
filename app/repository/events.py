from typing import Optional
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event import Event
from app.common.context import AppContext
from app.common.middleware.logger import Logger
from app.common.schemas.events import (
    EventCreate,
    EventCreateDomain,
    EventDetailInfo,
    EventQuery,
)

logger = Logger()


class EventRepository:

    def __init__(self) -> None:
        pass

    def _prepare_query(self, query: EventQuery, stmt: Select) -> Select:

        if query.id is not None:
            stmt = stmt.where(Event.id == query.id)
        if query.page is not None and query.page_size is not None:
            offset = (query.page - 1) * query.page_size
            stmt = stmt.offset(offset).limit(query.page_size)
        if query.group_id is not None:
            stmt = stmt.where(Event.group_id == query.group_id)
        if query.name is not None:
            stmt = stmt.where(Event.name == query.name)
        if query.start_time is not None:
            stmt = stmt.where(Event.start_time >= query.start_time)
        if query.end_time is not None:
            stmt = stmt.where(Event.end_time <= query.end_time)
        if query.priority is not None:
            stmt = stmt.where(Event.priority == query.priority)
        if query.category is not None:
            stmt = stmt.where(Event.category == query.category)
        if query.owner_id is not None:
            stmt = stmt.where(Event.owner_id == query.owner_id)
        return stmt

    async def create(
        self, session: AsyncSession, event_create: EventCreateDomain, ctx: AppContext
    ) -> EventDetailInfo:
        new_event = Event()
        new_event.name = event_create.name
        new_event.destination = event_create.destination
        new_event.cost = event_create.cost
        new_event.group_id = event_create.group_id
        new_event.owner_id = event_create.owner_id
        new_event.start_time = event_create.start_time
        new_event.end_time = event_create.end_time
        new_event.priority = event_create.priority
        new_event.category = event_create.category
        session.add(new_event)
        await session.flush()
        return new_event.viewInfo()

    async def get(
        self, session: AsyncSession, event_query: EventQuery, ctx: AppContext
    ) -> Optional[EventDetailInfo]:
        stmt = select(Event)
        stmt = self._prepare_query(event_query, stmt)
        result = await session.execute(stmt)
        event = result.scalars().first()

        return event.viewInfo() if event else None
