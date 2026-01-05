from enum import Enum


class RoomType(str, Enum):
    RoomTypeStandard = "Standard"
    RoomTypeDeluxe = "Deluxe"
    RoomTypeSuite = "Suite"
    RoomTypeExecutive = "Executive"
