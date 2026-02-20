from typing import List
from fastapi import APIRouter, status

from app.common.schemas.events import EventCalendarView, EventDetailInfo
from app.handler.event import EventHandler


class EventRouter:
    route: APIRouter
    handler: EventHandler

    def __init__(self, handler: EventHandler) -> None:
        self.route = APIRouter(prefix="", tags=["Events"])
        self.handler = handler

        self.route.add_api_route(
            path="/calendar",
            endpoint=self.handler.list_calendar_events,
            methods=["GET"],
            response_model=List[EventCalendarView],
            status_code=status.HTTP_200_OK,
            summary="List calendar events",
            description="List calendar events for a given month and year",
        )

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
                                "destination": "Event 1 destination",
                                "cost": "Event 1 cost",
                                "start_time": "2026-01-01T00:00:00Z",
                                "end_time": "2026-01-01T00:00:00Z",
                                "priority": "Event 1 priority",
                                "category": "Event 1 category",
                                "owner_id": "550e8400-e29b-41d4-a716-446655440000",
                                "group_id": "550e8400-e29b-41d4-a716-446655440000",
                                "created_at": "2026-01-01T00:00:00Z",
                                "updated_at": "2026-01-01T00:00:00Z",
                                "tags": [
                                    {
                                        "id": "550e8400-e29b-41d4-a716-446655440000",
                                        "name": "Tag 1",
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
