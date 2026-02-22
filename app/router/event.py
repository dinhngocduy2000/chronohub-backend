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
            path="/",
            endpoint=self.handler.list_calendar_events,
            methods=["GET"],
            response_model=List[EventCalendarView],
            status_code=status.HTTP_200_OK,
            summary="List calendar events",
            description="List calendar events for a given month and year",
        )

        self.route.add_api_route(
            path="/{id}",
            endpoint=self.handler.get_event_detail,
            methods=["GET"],
            response_model=EventDetailInfo,
            status_code=status.HTTP_200_OK,
            summary="Get event detail",
            description="Get event detail by id",
        )

        self.route.add_api_route(
            path="/",
            endpoint=self.handler.create_event,
            methods=["POST"],
            response_model=EventDetailInfo,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new event",
            description="Create a new event with name, description, and members",
            response_description="The created event information",
        )

        self.route.add_api_route(
            path="/{id}",
            endpoint=self.handler.delete_event,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete an event",
            description="Delete an event by id",
        )

        self.route.add_api_route(
            path="/{id}",
            endpoint=self.handler.update_event,
            methods=["PUT"],
            response_model=str,
            status_code=status.HTTP_200_OK,
            summary="Update an event",
            description="Update an event by id",
        )
