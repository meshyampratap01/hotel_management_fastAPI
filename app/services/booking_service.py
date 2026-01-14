import uuid
from typing import List

from fastapi import Depends, status

from app.app_exception.app_exception import AppException
from app.dtos.booking_requests import CreateBookingRequest
from app.models.bookings import Booking, BookingStatus
from app.repository.booking_repository import BookingRepository
from app.repository.room_repository import RoomRepository
from sqs_event_publisher import event_publisher


class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository = Depends(BookingRepository),
        room_repo: RoomRepository = Depends(RoomRepository),
    ):
        self.booking_repo = booking_repo
        self.room_repo = room_repo

    def book_room(
        self,
        request: CreateBookingRequest,
        current_user: dict,
    ) -> Booking:
        room_number = request.room_number
        check_in = request.check_in_date
        check_out = request.check_out_date

        room = self.room_repo.get_room_by_number(room_number)

        if not room.is_available:
            raise AppException(
                message="Room already booked",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_id = current_user.get("sub")
        if not user_id:
            raise AppException(
                message="Invalid user context",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        new_booking = Booking(
            id=str(uuid.uuid4()),
            user_id=user_id,
            room_id=room.id,
            room_num=room_number,
            check_in=check_in,
            check_out=check_out,
            status=BookingStatus.Booking_Status_Booked,
            food_req=False,
            clean_req=False,
        )

        try:
            self.room_repo.update_room_availability(room_number, False)
            self.booking_repo.save_booking(new_booking)
            return new_booking

        except AppException:
            raise

    def cancel_booking(self, booking_id: str) -> None:
        try:
            booking = self.booking_repo.get_booking_by_ID(booking_id)
        except AppException:
            raise

        if booking.status == BookingStatus.Booking_Status_Cancelled.value:
            raise AppException(
                message="booking already cancelled",
                status_code=status.HTTP_409_CONFLICT,
            )

        booking.status = BookingStatus.Booking_Status_Cancelled
        self.room_repo.update_room_availability(booking.room_num, True)
        self.booking_repo.update_booking(booking)

        if booking.clean_req or booking.food_req:
            event_pub = event_publisher.BookingEventPublisher()
            event_pub.publish_booking_cancelled(booking)

    def get_active_bookings_by_user(self, user_id: str) -> List[Booking]:
        return self.booking_repo.get_bookings_by_userID(user_id)
