from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class BookingStatus(str, Enum):
    Booking_Status_Booked = "Booked"
    Booking_Status_Cancelled = "Cancelled"
    Booking_Status_Completed = "Completed"


class Booking(BaseModel):
    id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    room_id: str = Field(..., min_length=1)

    room_num: int = Field(..., ge=1)

    check_in: date
    check_out: date

    status: BookingStatus

    food_req: bool
    clean_req: bool

    model_config = ConfigDict(extra="ignore")
