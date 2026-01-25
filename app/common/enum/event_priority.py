from enum import Enum


class EventPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
