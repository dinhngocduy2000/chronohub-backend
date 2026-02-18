from datetime import timedelta
from uuid import UUID
from app.common.context import AppContext
from app.common.exceptions import BadRequestException
from app.common.middleware.logger import Logger
from app.common.schemas.events import (
    EventCreate,
    EventCreateDomain,
    EventDetailInfo,
    EventQuery,
)
from app.common.schemas.user import Credential
from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession

logger = Logger()


class EventService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

    async def create_event(
        self, event_create: EventCreate, ctx: AppContext
    ) -> EventDetailInfo:
        async def _create_event(session: AsyncSession) -> EventDetailInfo:
            try:
                logger.info(
                    msg=f"Checking if there is an event within the time span and same owner and group...",
                    context=ctx,
                )
                event_within_time_span_same_owner_group = (
                    await self.repo.event_repo().get(
                        event_query=EventQuery(
                            start_time=event_create.start_time,
                            end_time=event_create.end_time,
                            group_id=event_create.group_id,
                            owner_id=ctx.actor,
                        ),
                        session=session,
                        ctx=ctx,
                    )
                )
                if event_within_time_span_same_owner_group is not None:
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
                event_duration = event_create.end_time - event_create.start_time

                if event_duration < timedelta(seconds=0):
                    logger.error(msg="Event end time must be after start time")
                    raise BadRequestException(
                        message="Event end time must be after start time"
                    )

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
                new_event = await self.repo.event_repo().create(
                    session=session,
                    event_create=EventCreateDomain(
                        **event_create.model_dump(mode="python"),
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
