from uuid import uuid4

from fastapi import Depends

from app.common.context import AppContext
from app.common.enum.context_actions import SEND_EMAIL
from app.common.exceptions import BadRequestException
from app.common.exceptions.decorator import exception_handler
from app.common.middleware.auth_middleware import AuthMiddleware
from app.common.middleware.logger import Logger
from app.common.schemas.mail import SendMailRequest, SendMailResponse
from app.common.schemas.user import Credential
from app.external.base import ExternalService

logger = Logger()


class MailHandler:
    service: ExternalService[SendMailRequest, SendMailResponse]

    def __init__(
        self, service: ExternalService[SendMailRequest, SendMailResponse]
    ) -> None:
        self.service = service

    @exception_handler
    async def send_email(
        self,
        request: SendMailRequest,
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> SendMailResponse:
        ctx = AppContext(trace_id=uuid4(), action=SEND_EMAIL, actor=credential.id)
        logger.info(
            msg=f"Received send email request from user {credential.id}", context=ctx
        )

        result = await self.service.send(request=request, ctx=ctx)

        if not result.success:
            raise BadRequestException(message=result.message)

        return result
