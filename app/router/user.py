from typing import List
from fastapi import APIRouter, status, Query, Path
from app.handler.user import UserHandler
from app.common.schemas.user import UserCreate, UserInfo, UserLoginResponse


class UserRouter:
    router: APIRouter
    handler: UserHandler

    def __init__(self, handler: UserHandler) -> None:
        self.router = APIRouter(prefix="", tags=["Users"])
        self.handler = handler
