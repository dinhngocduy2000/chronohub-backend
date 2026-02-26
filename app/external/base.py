from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.common.context import AppContext

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class ExternalService(ABC, Generic[TRequest, TResponse]):
    """
    Abstract base class for all external service integrations.

    To add a new external service (e.g., SMS, push notification, payment):
      1. Define request/response schemas
      2. Create a subclass implementing `send()`
      3. Inject the subclass where needed via the App wiring in main.py
    """

    @abstractmethod
    async def send(self, request: TRequest, ctx: AppContext) -> TResponse:
        raise NotImplementedError
