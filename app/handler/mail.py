from datetime import datetime
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
from app.common.utils.generate_otp import generate_otp
from app.external.base import ExternalService
from app.external.mail.jinja_templates import render_mail_html
from app.core.config import settings

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
        credential: Credential = Depends(AuthMiddleware.auth_middleware),
    ) -> SendMailResponse:
        ctx = AppContext(trace_id=uuid4(), action=SEND_EMAIL, actor=credential.id)
        logger.info(
            msg=f"Received send email request from user {credential.id}", context=ctx
        )
        html = render_mail_html(
            "send-otp.html",
            name="Dylan",
            app_name=settings.APP_NAME,
            action_url="https://example.com/onboarding",
            subject="Welcome to Chronohub",
            otp=generate_otp(),
            expiry_minutes=10,
            year=datetime.now().year,
            base_url=settings.email_public_base_url,
        )
        request = SendMailRequest(
            to=["ngocduydinh2000@gmail.com"],
            subject="Welcome to Chronohub",
            body="Hi Alex, thanks for joining. Get started: https://example.com/onboarding",
            html=html,
        )
        result = await self.service.send(request=request, ctx=ctx)

        if not result.success:
            raise BadRequestException(message=result.message)

        return result
