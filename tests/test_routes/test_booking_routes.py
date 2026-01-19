from datetime import date, timedelta
import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.app import app
from app.services.booking_service import BookingService
from app.dependencies import get_ddb_resource, get_table_name


class TestBookingRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_booking_service = Mock(spec=BookingService)

        self.mock_user = {
            "sub": "user-123",
            "userName": "test_user",
            "role": "Guest",
        }

        app.dependency_overrides[BookingService] = lambda: self.mock_booking_service
        app.dependency_overrides[get_ddb_resource] = lambda: Mock()
        app.dependency_overrides[get_table_name] = lambda: "BookingsTable"

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_book_room_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "fake-token"
        mock_verify_jwt.return_value = self.mock_user

        booking_response = {
            "id": "booking-1",
            "room_number": 101,
        }

        self.mock_booking_service.book_room.return_value = booking_response

        payload = {
            "room_number": 101,
            "check_in_date": date.today().isoformat(),
            "check_out_date": (date.today() + timedelta(days=1)).isoformat(),
        }

        response = self.client.post("/bookings/bookRoom", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "Room Booked Successfully")
        self.assertEqual(response.json()["data"], booking_response)

        self.mock_booking_service.book_room.assert_called_once()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_cancel_booking_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "fake-token"
        mock_verify_jwt.return_value = self.mock_user

        booking_id = "booking-123"

        response = self.client.delete(f"/bookings/{booking_id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Booking Cancelled Successfully")

        self.mock_booking_service.cancel_booking.assert_called_once_with(booking_id)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_bookings_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "fake-token"
        mock_verify_jwt.return_value = self.mock_user

        bookings_response = [
            {
                "id": "booking-1",
                "room_number": 101,
            },
            {
                "id": "booking-2",
                "room_number": 102,
            },
        ]

        self.mock_booking_service.get_active_bookings_by_user.return_value = (
            bookings_response
        )

        response = self.client.get("/bookings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Bookings Fetched Successfully")
        self.assertEqual(response.json()["data"], bookings_response)

        self.mock_booking_service.get_active_bookings_by_user.assert_called_once_with(
            "user-123"
        )
