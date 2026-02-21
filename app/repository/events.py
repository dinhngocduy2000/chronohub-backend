from datetime import datetime
from typing import List, Optional
from sqlalchemy import Select, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.event import Event
from app.common.context import AppContext
from app.common.middleware.logger import Logger
from app.common.schemas.events import (
    EventCreateDomain,
    EventDetailInfo,
    EventJoinOptions,
    EventListInfo,
    EventQuery,
    ListEventQuery,
)

logger = Logger()


class EventRepository:

    def __init__(self) -> None:
        pass

    def _prepare_query(
        self, query: EventQuery, stmt: Select, ctx: AppContext
    ) -> Select:

        if query.id is not None:
            logger.info(msg=f"Prepare query: ID: {query.id}", context=ctx)
            stmt = stmt.where(Event.id == query.id)
        if query.page is not None and query.page_size is not None:
            offset = (query.page - 1) * query.page_size
            logger.info(
                msg=f"Prepare query: Offset: {offset}, Page size: {query.page_size}",
                context=ctx,
            )
            stmt = stmt.offset(offset).limit(query.page_size)
        if query.group_id is not None:
            logger.info(msg=f"Prepare query: Group ID: {query.group_id}", context=ctx)
            stmt = stmt.where(Event.group_id == query.group_id)
        if query.name is not None:
            logger.info(msg=f"Prepare query: Name: {query.name}", context=ctx)
            stmt = stmt.where(Event.name == query.name)
        if query.start_time is not None:
            logger.info(
                msg=f"Prepare query: Start time: {query.start_time}", context=ctx
            )
            stmt = stmt.where(Event.start_time >= query.start_time)
        if query.end_time is not None:
            logger.info(msg=f"Prepare query: End time: {query.end_time}", context=ctx)
            stmt = stmt.where(Event.end_time <= query.end_time)
        if query.priority is not None:
            logger.info(msg=f"Prepare query: Priority: {query.priority}", context=ctx)
            stmt = stmt.where(Event.priority == query.priority)
        if query.category is not None:
            logger.info(msg=f"Prepare query: Category: {query.category}", context=ctx)
            stmt = stmt.where(Event.category == query.category)
        if query.owner_id is not None:
            logger.info(msg=f"Prepare query: Owner ID: {query.owner_id}", context=ctx)
            stmt = stmt.where(Event.owner_id == query.owner_id)
        return stmt

    def _prepare_join(
        self, stmt: Select, options: Optional[EventJoinOptions]
    ) -> Select:
        if options is not None:
            # if options.include_tags:
            #     stmt = stmt.options(joinedload(Event.tags))
            if options.include_owner:
                stmt = stmt.options(joinedload(Event.owner))
        return stmt

    async def create(
        self, session: AsyncSession, event_create: EventCreateDomain, ctx: AppContext
    ) -> EventDetailInfo:
        try:
            # Use mode='python' to ensure proper UUID serialization
            # Exclude 'tags' from dump since it's a relationship, not a column
            event_data = event_create.model_dump(mode="python", exclude={"tags"})
            new_event = Event(**event_data)
            session.add(new_event)
            await session.flush()
            await session.refresh(new_event)

            return new_event.viewInfo()
        except Exception as e:
            logger.error(msg=f"Create event repository: Exception: {e}", context=ctx)
            raise e

    async def get(
        self,
        session: AsyncSession,
        query: EventQuery,
        ctx: AppContext,
        options: Optional[EventJoinOptions],
    ) -> Optional[Event]:
        try:
            stmt = select(Event)
            stmt = self._prepare_join(stmt=stmt, options=options)
            stmt = self._prepare_query(query=query, stmt=stmt, ctx=ctx)
            result = await session.execute(stmt)
            event: Event = result.scalars().first()

            return event
        except Exception as e:
            logger.error(msg=f"Get event repository: Exception: {e}", context=ctx)
            raise e

    async def list(
        self,
        session: AsyncSession,
        query: ListEventQuery,
        ctx: AppContext,
        options: Optional[EventJoinOptions],
    ) -> List[EventListInfo]:
        try:
            stmt = select(Event)

            stmt = self._prepare_join(stmt=stmt, options=options)
            stmt = stmt.order_by(Event.start_time)
            stmt = stmt.where(
                extract("month", Event.start_time) == query.month,
                extract("year", Event.start_time) == query.year,
            )
            if query.owner_id is not None:
                stmt = stmt.where(Event.owner_id == query.owner_id)

            if query.group_id is not None:
                stmt = stmt.where(Event.group_id == query.group_id)

            result = await session.execute(stmt)
            events = result.scalars().all()
            return [event.viewList() for event in events] if len(events) > 0 else []
        except Exception as e:
            logger.error(msg=f"List event repository: Exception: {e}", context=ctx)
            raise e
