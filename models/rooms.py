from dataclasses import dataclass
from models import room_types


@dataclass
class Room:
    id: str
    number: int
    type: room_types.RoomType
    price: int
    is_available: bool
    description: str
