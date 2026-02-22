from datetime import datetime, timedelta
from itertools import groupby
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import String
from app.common.context import AppContext
from app.common.exceptions import BadRequestException
from app.common.middleware.logger import Logger
from app.common.schemas.events import (
    EventCalendarView,
    EventCreate,
    EventCreateDomain,
    EventDetailInfo,
    EventJoinOptions,
    EventListInfo,
    EventQuery,
    ListEventQuery,
)
from app.common.schemas.user import Credential
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession

logger = Logger()


class EventService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

    async def _check_event_exists(
        self, query: EventQuery, session: AsyncSession, ctx: AppContext
    ):
        event_within_time_span_same_group = await self.repo.event_repo().get(
            session=session,
            query=query,
            ctx=ctx,
            options=EventJoinOptions(include_owner=False),
        )

        if event_within_time_span_same_group is not None:
            logger.error(
                msg=f"There is an event(s) within the time span",
                context=ctx,
            )
            raise BadRequestException(
                message="There is an event(s) within the time span"
            )

        logger.info(
            msg=f"No event(s) within the time span, checking for event duration...",
            context=ctx,
        )

    async def _check_event_duration(self, event_duration: timedelta, ctx: AppContext):
        if event_duration < timedelta(seconds=0):
            logger.error(msg="Event end time must be after start time")
            raise BadRequestException(message="Event end time must be after start time")

        if event_duration < timedelta(minutes=15):
            logger.error(
                msg=f"Event duration must be at least 15 minutes",
                context=ctx,
            )
            raise BadRequestException(
                message="Event duration must be at least 15 minutes"
            )

        logger.info(
            msg=f"Event duration is valid, creating event...",
            context=ctx,
        )

    async def create_event(
        self, event_create: EventCreate, ctx: AppContext
    ) -> EventDetailInfo:
        async def _create_event(session: AsyncSession) -> EventDetailInfo:
            try:
                logger.info(
                    msg=f"Checking if there is an event within the time span and same owner and group...",
                    context=ctx,
                )

                await self._check_event_exists(
                    query=EventQuery(
                        start_time=event_create.start_time,
                        end_time=event_create.end_time,
                        group_id=event_create.group_id,
                        owner_id=ctx.actor,
                    ),
                    session=session,
                    ctx=ctx,
                )

                event_duration = event_create.end_time - event_create.start_time

                await self._check_event_duration(event_duration=event_duration, ctx=ctx)

                new_event = await self.repo.event_repo().create(
                    session=session,
                    event_create=EventCreateDomain(
                        **event_create.model_dump(mode="python"),
                        id=uuid4(),
                        owner_id=ctx.actor,
                    ),
                    ctx=ctx,
                )
                logger.info(
                    msg=f"Event created successfully: {new_event.__dict__}",
                    context=ctx,
                )
                return new_event
            except Exception as e:
                logger.error(msg=f"Create event: Exception: {e}", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_create_event)

    async def list_calendar_events(
        self, query: ListEventQuery, ctx: AppContext
    ) -> List[EventCalendarView]:
        async def _list_calendar_events(
            session: AsyncSession,
        ) -> List[EventCalendarView]:
            try:
                events = await self.repo.event_repo().list(
                    session=session,
                    query=query,
                    ctx=ctx,
                    options=EventJoinOptions(include_tags=False),
                )

                calendar_events = [
                    EventCalendarView(date=day, events=list(group))
                    for day, group in groupby(events, key=lambda e: e.start_time.date())
                ]

                return calendar_events
            except Exception as e:
                logger.error(
                    msg=f"List calendar events service: Exception: {e}", context=ctx
                )
                raise e

        return await self.repo.transaction_wrapper(_list_calendar_events)

    async def get_event_detail(
        self, query: EventQuery, ctx: AppContext
    ) -> EventDetailInfo:
        async def _get_event_detail(session: AsyncSession) -> EventDetailInfo:
            try:
                event = await self.repo.event_repo().get(
                    session=session,
                    query=query,
                    ctx=ctx,
                    options=EventJoinOptions(include_owner=True, include_tags=True),
                )

                if event is None:
                    logger.error(msg=f"Event with id {query.id} not found", context=ctx)
                    raise BadRequestException(message="Event not found")

                event_info = event.viewInfo()
                event_info.owner = event.owner.view()

                logger.info(msg=f"Event detail info: {event_info}", context=ctx)
                return event_info
            except Exception as e:
                logger.error(
                    msg=f"Get event detail service: Exception: {e}", context=ctx
                )
                raise e

        return await self.repo.transaction_wrapper(_get_event_detail)
