from app.repository.registry import Registry
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    repo: Registry

    def __init__(self, repo: Registry) -> None:
        self.repo = repo

    async def create_user(self) -> None:
        async def _create_user(session: AsyncSession) -> None:
            await self.repo.user_repo().create_user(session=session)
            return

        return await self.repo.transaction_wrapper(_create_user)
