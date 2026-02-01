from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, Request
import jwt
from app.common.enum.user_status import UserStatus
from app.common.schemas.user import Credential
from app.core.config import settings
from app.services.auth import AuthService


class AuthMiddleware:
    auth_service: AuthService

    @classmethod
    def init(self, auth_service: AuthService):
        self.auth_service = auth_service

    @classmethod
    async def auth_middleware(self, request: Request) -> Credential:
        access_token = request.cookies.get("access_token")
        if access_token is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        decoded_token = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        exp_time = decoded_token["exp"]
        user_id = uuid.UUID(decoded_token["id"])
        if datetime.now(timezone.utc) > datetime.fromtimestamp(exp_time, timezone.utc):
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_info = await self.auth_service.get_current_user(user_id)
        if user_info is None:
            raise HTTPException(status_code=401, detail="Unauthorized")

        credenttial: Credential = Credential(
            id=user_info.id,
            email=user_info.email,
            is_pending=user_info.status == UserStatus.PENDING,
        )

        return credenttial
