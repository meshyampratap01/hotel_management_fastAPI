import unittest
from unittest.mock import MagicMock
from datetime import date, timedelta

from fastapi import status

from app.services.booking_service import BookingService
from app.app_exception.app_exception import AppException
from app.models.bookings import BookingStatus
from app.dtos.booking_requests import CreateBookingRequest


class TestBookingService(unittest.TestCase):
    def setUp(self):
        self.mock_booking_repo = MagicMock()
        self.mock_room_repo = MagicMock()

        self.service = BookingService(
            booking_repo=self.mock_booking_repo,
            room_repo=self.mock_room_repo,
        )

        self.valid_user = {"sub": "user-123"}

        self.valid_request = CreateBookingRequest(
            room_number=101,
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=1),
        )

    def test_book_room_success(self):
        room = MagicMock()
        room.id = "room-1"
        room.is_available = True

        self.mock_room_repo.get_room_by_number.return_value = room

        booking = self.service.book_room(
            request=self.valid_request,
            current_user=self.valid_user,
        )

        self.assertEqual(booking.user_id, "user-123")
        self.assertEqual(booking.room_num, 101)
        self.assertEqual(booking.status, BookingStatus.Booking_Status_Booked)

        self.mock_room_repo.update_room_availability.assert_called_once_with(101, False)
        self.mock_booking_repo.save_booking.assert_called_once()

    def test_book_room_room_not_available(self):
        room = MagicMock()
        room.is_available = False

        self.mock_room_repo.get_room_by_number.return_value = room

        with self.assertRaises(AppException) as ctx:
            self.service.book_room(self.valid_request, self.valid_user)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "Room already booked")

    def test_book_room_invalid_user_context(self):
        room = MagicMock()
        room.id = "room-1"
        room.is_available = True

        self.mock_room_repo.get_room_by_number.return_value = room

        with self.assertRaises(AppException) as ctx:
            self.service.book_room(self.valid_request, current_user={})

        self.assertEqual(ctx.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(ctx.exception.message, "Invalid user context")

    def test_book_room_repo_exception_propagates(self):
        room = MagicMock()
        room.id = "room-1"
        room.is_available = True

        self.mock_room_repo.get_room_by_number.return_value = room
        self.mock_booking_repo.save_booking.side_effect = AppException(
            message="DB error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        with self.assertRaises(AppException):
            self.service.book_room(self.valid_request, self.valid_user)

    def test_cancel_booking_success(self):
        booking = MagicMock()
        booking.status = BookingStatus.Booking_Status_Booked
        booking.room_num = 101

        self.mock_booking_repo.get_booking_by_ID.return_value = booking

        self.service.cancel_booking("booking-123")

        self.assertEqual(booking.status, BookingStatus.Booking_Status_Cancelled)

        self.mock_room_repo.update_room_availability.assert_called_once_with(101, True)
        self.mock_booking_repo.update_booking.assert_called_once_with(booking)

    def test_cancel_booking_already_cancelled(self):
        booking = MagicMock()
        booking.status = BookingStatus.Booking_Status_Cancelled.value

        self.mock_booking_repo.get_booking_by_ID.return_value = booking

        with self.assertRaises(AppException) as ctx:
            self.service.cancel_booking("booking-123")

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ctx.exception.message, "booking already cancelled")

    def test_get_active_bookings_by_user(self):
        bookings = [MagicMock(), MagicMock()]
        self.mock_booking_repo.get_bookings_by_userID.return_value = bookings

        result = self.service.get_active_bookings_by_user("user-123")

        self.assertEqual(result, bookings)
        self.mock_booking_repo.get_bookings_by_userID.assert_called_once_with(
            "user-123"
        )
