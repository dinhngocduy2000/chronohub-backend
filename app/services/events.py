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
                event_within_time_span_same_owner_group = (
                    await self.repo.event_repo().get(
                        event_query=EventQuery(
                            start_time=event_create.start_time,
                            end_time=event_create.end_time,
                            group_id=event_create.group_id,
                            owner_id=event_create.owner_id,
                        ),
                        session=session,
                    )
                )
                if event_within_time_span_same_owner_group is not None:
                    raise BadRequestException(
                        message="There is an event(s) within the time span"
                    )

                event_duration = event_create.end_time - event_create.start_time
                if event_duration < timedelta(minutes=15):
                    raise BadRequestException(
                        message="Event duration must be at least 15 minutes"
                    )

                new_event = self.repo.event_repo().create(
                    session=session,
                    event_create=EventCreateDomain(
                        **event_create.model_dump(),
                        owner_id=UUID(ctx.actor),
                    ),
                    ctx=ctx,
                )
                return new_event
            except Exception as e:
                logger.error(msg=f"Create event: Exception: {e}", context=ctx)
                raise e

        return await self.repo.transaction_wrapper(_create_event)
