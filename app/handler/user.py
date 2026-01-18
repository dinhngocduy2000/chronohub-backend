from app.services.user import UserService


class UserHandler:
    service: UserService

    def __init__(self, service: UserService) -> None:
        self.service = service

    async def create_user(self) -> None:
        return await self.service.create_user()
