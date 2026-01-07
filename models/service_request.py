from dataclasses import dataclass
from enum import Enum


class ServiceType(str, Enum):
    CLEANING = "Cleaning"
    FOOD = "Food"


class ServiceStatus(str, Enum):
    PENDING = "Pending"
    DONE = "Done"


@dataclass
class ServiceRequest:
    id: str
    user_id: str
    booking_id: str
    room_num: int
    type: ServiceType
    status: ServiceStatus
    is_assigned: bool
    assigned_to: str | None
    details: str
