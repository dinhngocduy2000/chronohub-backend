from sqlalchemy.ext.asyncio import AsyncSession

from app.common.context import AppContext
from app.common.schemas.events import EventTagCreate
from app.common.middleware.logger import Logger
from app.models.event_tag import EventTag

logger = Logger()


class EventTagRepository:
    def __init__(self) -> None:
        pass

    async def create(
        self, session: AsyncSession, event_tag: EventTagCreate, ctx: AppContext
    ) -> None:
        try:
            event_tag = EventTag(**event_tag.model_dump(mode="python"))
            session.add(event_tag)
            await session.flush()
            await session.refresh(event_tag)
            return
        except Exception as e:
            logger.error(
                msg=f"Create event tag repository: Exception: {e}", context=ctx
            )
            raise e
