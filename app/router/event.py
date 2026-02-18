from fastapi import APIRouter, status

from app.common.schemas.events import EventDetailInfo
from app.handler.event import EventHandler


class EventRouter:
    route: APIRouter
    handler: EventHandler

    def __init__(self, handler: EventHandler) -> None:
        self.route = APIRouter(prefix="", tags=["Events"])
        self.handler = handler

        self.route.add_api_route(
            path="/create",
            endpoint=self.handler.create_event,
            methods=["POST"],
            response_model=EventDetailInfo,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new event",
            description="Create a new event with name, description, and members",
            response_description="The created event information",
            responses={
                201: {
                    "description": "Event created successfully",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "name": "Event 1",
                                "description": "Event 1 description",
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
