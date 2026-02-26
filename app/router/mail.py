from fastapi import APIRouter, status

from app.common.schemas.mail import SendMailResponse
from app.handler.mail import MailHandler


class MailRouter:
    router: APIRouter
    handler: MailHandler

    def __init__(self, handler: MailHandler) -> None:
        self.router = APIRouter(prefix="", tags=["Mail"])
        self.handler = handler

        self.router.add_api_route(
            path="/send",
            endpoint=self.handler.send_email,
            methods=["POST"],
            response_model=SendMailResponse,
            status_code=status.HTTP_200_OK,
            summary="Send an email",
            description="Send an email to one or more recipients. Requires authentication.",
            response_description="The result of the email send operation",
            responses={
                200: {
                    "description": "Email sent successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "success": True,
                                "message": "Email sent successfully",
                            }
                        }
                    },
                },
                400: {
                    "description": "Failed to send email",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Failed to send email: SMTP error"}
                        }
                    },
                },
            },
        )
