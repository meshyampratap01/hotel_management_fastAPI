import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from fastapi import status

from app.models import service_request
from app.services.service_request_service import ServiceRequestService
from app.app_exception.app_exception import AppException
from app.models.service_request import ServiceStatus, ServiceRequest
from app.dtos.service_request import (
    CreateServiceRequest,
    UpdateServiceRequestStatus,
    assign_service_request_dto,
    AssignedPendingServiceRequestDTO,
)


class TestServiceRequestService(unittest.TestCase):
    def setUp(self):
        self.mock_service_repo = MagicMock()
        self.mock_booking_repo = MagicMock()
        self.mock_user_repo = MagicMock()

        self.service = ServiceRequestService(
            service_request_repo=self.mock_service_repo,
            booking_repo=self.mock_booking_repo,
            user_repo=self.mock_user_repo,
        )

        self.current_user = {"sub": "user-123"}

    @patch("app.services.service_request_service.uuid.uuid4")
    def test_create_service_request_internal(self, mock_uuid):
        mock_uuid.return_value = "sr-uuid"
        now = datetime(2026, 1, 10)

        req = self.service._create_service_request(
            room_num=101,
            type=service_request.ServiceType.CLEANING,
            details="AC issue",
            user_id="user-123",
            booking_id="booking-1",
            created_at=now,
        )

        self.assertIsInstance(req, ServiceRequest)
        self.assertEqual(req.id, "sr-uuid")
        self.assertEqual(req.room_num, 101)
        self.assertEqual(req.user_id, "user-123")
        self.assertEqual(req.booking_id, "booking-1")
        self.assertEqual(req.status, ServiceStatus.PENDING)
        self.assertFalse(req.is_assigned)
        self.assertIsNone(req.assigned_to)
        self.assertEqual(req.created_at, now)

    @patch("app.services.service_request_service.uuid.uuid4")
    @patch("app.services.service_request_service.datetime")
    def test_save_service_request_success(self, mock_datetime, mock_uuid):
        mock_uuid.return_value = "sr-uuid"
        mock_datetime.now.return_value = datetime(2026, 1, 10)

        booking = MagicMock()
        booking.room_num = 101
        booking.id = "booking-1"

        self.mock_booking_repo.get_bookings_by_userID.return_value = [booking]

        request = CreateServiceRequest(
            room_num=101,
            type=service_request.ServiceType.CLEANING,
            details="Need cleaning",
        )

        self.service.save_service_request(request, self.current_user)

        self.mock_service_repo.save_service_request.assert_called_once()

    def test_save_service_request_no_bookings(self):
        self.mock_booking_repo.get_bookings_by_userID.return_value = []

        request = CreateServiceRequest(
            room_num=101,
            type=service_request.ServiceType.CLEANING,
            details="Test",
        )

        with self.assertRaises(AppException) as ctx:
            self.service.save_service_request(request, self.current_user)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "No active bookings found")

    def test_save_service_request_invalid_room(self):
        booking = MagicMock()
        booking.room_num = 102
        booking.id = "booking-1"

        self.mock_booking_repo.get_bookings_by_userID.return_value = [booking]

        request = CreateServiceRequest(
            room_num=101,
            type=service_request.ServiceType.CLEANING,
            details="Test",
        )

        with self.assertRaises(AppException) as ctx:
            self.service.save_service_request(request, self.current_user)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "Invalid room number")

    def test_get_all_pending_service_requests(self):
        requests = [MagicMock(), MagicMock()]
        self.mock_service_repo.get_all_pending_service_requests.return_value = requests

        result = self.service.get_all_pending_service_requests()

        self.assertEqual(result, requests)

    def test_get_service_request_by_user_id(self):
        requests = [MagicMock()]
        self.mock_service_repo.get_pending_service_requests_by_user_id.return_value = (
            requests
        )

        result = self.service.get_service_request_by_userID(self.current_user)

        self.assertEqual(result, requests)
        self.mock_service_repo.get_pending_service_requests_by_user_id.assert_called_once_with(
            "user-123"
        )

    def test_assign_service_request(self):
        request = assign_service_request_dto(employee_id="emp-123")

        self.mock_user_repo.get_user_by_id.return_value = MagicMock()

        self.service.assign_service_request("sr-1", request)

        self.mock_user_repo.get_user_by_id.assert_called_once_with("emp-123")
        self.mock_service_repo.assign_service_request.assert_called_once_with(
            "sr-1", "emp-123"
        )

    def test_get_assigned_service_requests(self):
        sr = MagicMock()
        sr.id = "sr-1"
        sr.user_id = "user-1"
        sr.room_num = 101
        sr.status = ServiceStatus.PENDING

        self.mock_service_repo.get_assigned_service_requests.return_value = [sr]

        result = self.service.get_assigned_service_requests({"sub": "emp-123"})

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], AssignedPendingServiceRequestDTO)
        self.assertEqual(result[0].service_request_id, "sr-1")

    def test_update_service_request_not_found(self):
        self.mock_service_repo.get_service_request_by_id.return_value = None

        request = UpdateServiceRequestStatus(status=ServiceStatus.DONE)

        with self.assertRaises(AppException) as ctx:
            self.service.update_service_request("sr-1", request)

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(ctx.exception.message, "Service request not found")

    def test_update_service_request_invalid_status(self):
        req = MagicMock()
        self.mock_service_repo.get_service_request_by_id.return_value = req

        request = UpdateServiceRequestStatus(status=ServiceStatus.PENDING)

        with self.assertRaises(AppException) as ctx:
            self.service.update_service_request("sr-1", request)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "Invalid status")

    def test_update_service_request_success(self):
        req = MagicMock()
        self.mock_service_repo.get_service_request_by_id.return_value = req

        request = UpdateServiceRequestStatus(status=ServiceStatus.DONE)

        self.service.update_service_request("sr-1", request)

        self.mock_service_repo.update_service_request.assert_called_once_with(
            "sr-1", ServiceStatus.DONE
        )
