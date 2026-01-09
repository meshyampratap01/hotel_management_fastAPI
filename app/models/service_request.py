from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ServiceType(str, Enum):
    CLEANING = "Cleaning"
    FOOD = "Food"


class ServiceStatus(str, Enum):
    PENDING = "Pending"
    DONE = "Done"


class ServiceRequest(BaseModel):
    id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    booking_id: str = Field(..., min_length=1)

    room_num: int = Field(..., ge=1)

    type: ServiceType
    status: ServiceStatus

    is_assigned: bool
    created_at: datetime
    assigned_to: Optional[str] = None

    details: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="ignore")
