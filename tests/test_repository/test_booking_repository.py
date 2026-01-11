import unittest
from unittest.mock import MagicMock
from datetime import date
from botocore.exceptions import ClientError
from fastapi import status

from app.repository.booking_repository import BookingRepository
from app.app_exception.app_exception import AppException
from app.models.bookings import Booking, BookingStatus


class TestBookingRepository(unittest.TestCase):
    def setUp(self):
        self.mock_ddb_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_ddb_client = MagicMock()

        self.mock_ddb_resource.Table.return_value = self.mock_table
        self.mock_ddb_resource.meta.client = self.mock_ddb_client

        self.repo = BookingRepository(
            ddb_resource=self.mock_ddb_resource,
            table_name="test-table",
        )

        self.booking = Booking(
            id="booking-1",
            user_id="user-1",
            room_id="room-1",
            room_num=101,
            check_in=date(2026, 1, 10),
            check_out=date(2026, 1, 12),
            status=BookingStatus.Booking_Status_Booked,
            food_req=False,
            clean_req=False,
        )

    def test_save_booking_success(self):
        self.repo.save_booking(self.booking)

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_save_booking_conflict(self):
        error_response = {
            "Error": {"Code": "TransactionCanceledException"},
            "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response=error_response,
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.save_booking(self.booking)

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_get_booking_by_id_success(self):
        self.mock_table.get_item.return_value = {
            "Item": self.booking.model_dump(mode="json")
        }

        result = self.repo.get_booking_by_ID("booking-1")

        self.assertEqual(result.id, "booking-1")

    def test_get_booking_by_id_not_found(self):
        self.mock_table.get_item.return_value = {}

        with self.assertRaises(AppException) as ctx:
            self.repo.get_booking_by_ID("booking-1")

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_booking_by_id_ddb_error(self):
        self.mock_table.get_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="GetItem",
        )

        with self.assertRaises(AppException):
            self.repo.get_booking_by_ID("booking-1")

    def test_update_booking_success(self):
        self.repo.update_booking(self.booking)

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_update_booking_not_found(self):
        error_response = {
            "Error": {"Code": "TransactionCanceledException"},
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response=error_response,
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.update_booking(self.booking)

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_bookings_by_user_id_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                self.booking.model_dump(mode="json"),
            ]
        }

        result = self.repo.get_bookings_by_userID("user-1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].user_id, "user-1")

    def test_get_bookings_by_user_id_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_bookings_by_userID("user-1")
