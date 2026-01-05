from dataclasses import dataclass
from datetime import datetime
from models import booking_status


@dataclass
class Booking:
    id: str
    user_id: str
    room_id: str
    room_num: int
    check_in: datetime
    check_out: datetime
    status: booking_status.BookingStatus
    food_req: bool
    clean_req: bool
