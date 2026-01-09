from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class RoomType(str, Enum):
    RoomTypeStandard = "Standard"
    RoomTypeDeluxe = "Deluxe"
    RoomTypeSuite = "Suite"
    RoomTypeExecutive = "Executive"


class Room(BaseModel):
    id: str = Field(..., min_length=1)
    number: int = Field(..., ge=1)

    type: RoomType

    price: int = Field(..., ge=0)
    is_available: bool

    description: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="ignore")
