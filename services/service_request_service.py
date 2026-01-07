import uuid

from fastapi import status
from app_exception.app_exception import AppException
from dtos.service_request import CreateServiceRequest, assign_service_request_dto
from models.bookings import Booking
from models.service_request import ServiceStatus, ServiceType, ServiceRequest
from repository.booking_repository import BookingRepository
from repository.service_request_repository import ServiceRequestRepository
from repository.user_repository import UserRepository


class ServiceRequestService:
    def __init__(
        self,
        service_request_repo: ServiceRequestRepository,
        booking_repo: BookingRepository,
        user_repo: UserRepository,
    ):
        self.service_request_repo = service_request_repo
        self.booking_repo = booking_repo
        self.user_repo = user_repo

    def _create_service_request(
        self,
        room_num: int,
        type: ServiceType,
        details: str,
        user_id: str,
        booking_id: str,
    ):
        return ServiceRequest(
            id=str(uuid.uuid4()),
            room_num=room_num,
            type=type,
            details=details,
            user_id=user_id,
            booking_id=booking_id,
            status=ServiceStatus.PENDING,
            is_assigned=False,
            assigned_to=None,
        )

    def save_service_request(self, request: CreateServiceRequest, current_user):
        user_id = current_user.get("sub")
        room_num = request.room_num

        bookings = self.booking_repo.get_bookings_by_userID(user_id)
        if not bookings:
            raise AppException(
                message="No active bookings found",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        valid_booking: Booking
        is_valid_room_num = False
        for booking in bookings:
            if booking.room_num == room_num:
                is_valid_room_num = True
                valid_booking = booking
                break

        if is_valid_room_num is False:
            raise AppException(
                message="Invalid room number",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        type = request.type
        details = request.details
        booking_id = valid_booking.id

        service_request = self._create_service_request(
            room_num, type, details, user_id, booking_id
        )

        try:
            self.service_request_repo.save_service_request(service_request)
        except Exception:
            raise

    def get_all_pending_service_requests(self):
        try:
            return self.service_request_repo.get_all_pending_service_requests()
        except Exception:
            raise

    def get_service_request_by_userID(self, current_user):
        user_id = current_user.get("sub")
        try:
            return self.service_request_repo.get_pending_service_requests_by_user_id(
                user_id
            )
        except Exception:
            raise

    def assign_service_request(
        self, service_request_id: str, request: assign_service_request_dto
    ):
        try:
            employee_id = request.employee_id
            _ = self.user_repo.get_user_by_id(employee_id)
            self.service_request_repo.assign_service_request(
                service_request_id, employee_id
            )
        except Exception:
            raise
