from dataclasses import dataclass
from datetime import date
from models import booking_status


@dataclass
class Booking:
    id: str
    user_id: str
    room_id: str
    room_num: int
    check_in: date
    check_out: date
    status: booking_status.BookingStatus
    food_req: bool
    clean_req: bool
