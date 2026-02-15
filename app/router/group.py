from fastapi import APIRouter, status

from app.common.schemas.group import GroupInfo
from app.handler.group import GroupHandler


class GroupRouter:
    router: APIRouter
    handler: GroupHandler

    def __init__(self, handler: GroupHandler) -> None:
        self.router = APIRouter(prefix="", tags=["Groups"])
        self.handler = handler

        self.router.add_api_route(
            path="/create",
            endpoint=self.handler.create_group,
            methods=["POST"],
            response_model=GroupInfo,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new group",
            description="Create a new group with name, description, and members",
            response_description="The created group information",
            responses={
                201: {
                    "description": "Group created successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "name": "Group 1",
                                "description": "Group 1 description",
                                "members": [
                                    {
                                        "id": "550e8400-e29b-41d4-a716-446655440000",
                                        "name": "User 1",
                                        "email": "user1@example.com",
                                    }
                                ],
                            }
                        }
                    },
                },
                400: {
                    "description": "Bad request - Invalid input data",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Invalid input data"}
                        }
                    },
                },
            },
        )
