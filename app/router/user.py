from fastapi import APIRouter

from app.handler.user import UserHandler


class UserRouter:
    router: APIRouter
    handler: UserHandler

    def __init__(self, handler: UserHandler) -> None:
        self.router = APIRouter()
        self.handler = handler
        self.router.add_api_route(
            path="",
            endpoint=self.handler.create_user,
            methods=["POST"],
            response_model=None,
            status_code=201,
            summary="Create a new user",
            description="Create a new user",
        )
