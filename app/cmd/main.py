from typing import Callable
from fastapi import FastAPI
from loguru import logger
from app.common.middleware.auth_middleware import AuthMiddleware
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import create_pg_engine
from app.handler.auth import AuthHandler
from app.handler.group import GroupHandler
from app.handler.user import UserHandler
from app.repository.registry import Registry
from app.router.auth import AuthRouter
from app.router.group import GroupRouter
from app.router.user import UserRouter
from app.services.auth import AuthService
from app.services.group import GroupService
from app.services.user import UserService


class App:
    application: FastAPI

    def on_init_app(self) -> Callable:
        async def start_app() -> None:
            pg_engine = create_pg_engine()
            registry = Registry(pg_engine)
            # ------------ Service ------------
            user_service = UserService(repo=registry)
            group_service = GroupService(repo=registry)
            auth_service = AuthService(repo=registry, group_service=group_service)

            AuthMiddleware.init(auth_service=auth_service)
            # ------------ Handler ------------
            user_handler = UserHandler(service=user_service)
            auth_handler = AuthHandler(service=auth_service)
            group_handler = GroupHandler(service=group_service)
            # ------------ Router ------------
            user_router = UserRouter(handler=user_handler)
            auth_router = AuthRouter(handler=auth_handler)
            group_router = GroupRouter(handler=group_handler)
            self.application.include_router(
                user_router.router,
                prefix=settings.API_V1_PREFIX + "/users",
                tags=["Users"],
            )
            self.application.include_router(
                auth_router.router,
                prefix=settings.API_V1_PREFIX + "/auth",
                tags=["Auth"],
            )
            self.application.include_router(
                group_router.router,
                prefix=settings.API_V1_PREFIX + "/groups",
                tags=["Groups"],
            )

        return start_app

    def on_terminate_app(self) -> Callable:
        @logger.catch
        async def stop_app() -> None:
            pass

        return stop_app

    def __init__(self) -> None:
        self.application = FastAPI(**settings.fastapi_kwargs)
        self.application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.application.add_event_handler("startup", self.on_init_app())
        self.application.add_event_handler("shutdown", self.on_terminate_app())


app = App().application
