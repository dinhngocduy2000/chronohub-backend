from typing import Callable
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.common.types import T
from app.repository.user import UserRepository


class Registry:
    _pg_engine: AsyncEngine
    _user_repo: UserRepository
    # _test_repo: TestRepository

    def __init__(self, pg_engine: AsyncEngine) -> None:
        self._pg_engine = pg_engine
        self._user_repo = UserRepository()
        # self._test_repo = TestRepository()

    async def transaction_wrapper(self, tx_func: Callable[[AsyncSession], T]) -> T:
        try:
            async_session = async_sessionmaker(self._pg_engine, expire_on_commit=False)
            session = async_session()
            await session.begin()
            res = await tx_func(session)
            await session.commit()
            return res
        except Exception as e:
            if session is not None and session.is_active:
                await session.rollback()
            raise e
        finally:
            if session is not None and session.is_active:
                await session.close()

    def user_repo(self) -> UserRepository:
        return self._user_repo
