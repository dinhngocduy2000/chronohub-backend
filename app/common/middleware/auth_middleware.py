from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, Request, status
import jwt
from app.common.context import AppContext
from app.common.enum.context_actions import AUTHENTICATE_USER
from app.common.enum.user_status import UserStatus
from app.common.middleware.logger import Logger
from app.common.schemas.user import Credential
from app.core.config import settings
from app.services.auth import AuthService

logger = Logger()


class AuthMiddleware:
    auth_service: AuthService

    @classmethod
    def init(self, auth_service: AuthService):
        self.auth_service = auth_service

    @classmethod
    async def auth_middleware(self, request: Request) -> Credential:
        ctx = AppContext(trace_id=uuid.uuid4(), action=AUTHENTICATE_USER)
        logger.info(msg=f"Getting token from cookies...", context=ctx)
        access_token = request.cookies.get("access_token")
        if access_token is None:
            logger.error(msg=f"Access token not found in cookies...", context=ctx)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )

        logger.info(msg=f"Token found, decoding token...", context=ctx)
        decoded_token = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        exp_time = decoded_token["exp"]
        user_id = uuid.UUID(decoded_token["id"])
        logger.info(
            msg=f"Token decoded successfully with user id {user_id}", context=ctx
        )
        if datetime.now(timezone.utc) > datetime.fromtimestamp(exp_time, timezone.utc):
            logger.error(msg=f"Token expired", context=ctx)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )

        user_info = await self.auth_service.get_current_user(user_id, ctx=ctx)
        if user_info is None:
            logger.error(msg=f"User with id {user_id} not found", context=ctx)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
            )

        logger.info(msg=f"User found, returning credential...", context=ctx)

        credenttial: Credential = Credential(
            id=user_info.id,
            email=user_info.email,
            is_pending=user_info.status == UserStatus.PENDING,
        )

        logger.info(msg=f"Credential authorized", context=ctx)

        return credenttial
