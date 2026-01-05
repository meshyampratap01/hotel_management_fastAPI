from enum import Enum


class BookingStatus(str, Enum):
    Booking_Status_Booked = "Booked"
    Booking_Status_Cancelled = "Cancelled"
    Booking_Status_Completed = "Completed"
