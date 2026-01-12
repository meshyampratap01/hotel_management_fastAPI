import uuid
from datetime import datetime

from fastapi import Depends, status
from typing import List
from app.app_exception.app_exception import AppException
from app.dtos.service_request import (
    AssignedPendingServiceRequestDTO,
    CreateServiceRequest,
    UpdateServiceRequestStatus,
    assign_service_request_dto,
)
from app.models.bookings import Booking
from app.models.service_request import ServiceStatus, ServiceType, ServiceRequest
from app.repository.booking_repository import BookingRepository
from app.repository.service_request_repository import ServiceRequestRepository
from app.repository.user_repository import UserRepository


class ServiceRequestService:
    def __init__(
        self,
        service_request_repo: ServiceRequestRepository = Depends(
            ServiceRequestRepository
        ),
        booking_repo: BookingRepository = Depends(BookingRepository),
        user_repo: UserRepository = Depends(UserRepository),
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
        created_at: datetime,
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
            created_at=created_at,
        )

    def save_service_request(self, request: CreateServiceRequest, current_user) -> None:
        user_id = current_user.get("sub")
        room_num = request.room_num

        bookings = self.booking_repo.get_bookings_by_userID(user_id)
        if not bookings:
            raise AppException(
                message="No active bookings found",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        valid_booking: Booking | None = None
        is_valid_room_num = False
        for booking in bookings:
            if booking.room_num == room_num:
                is_valid_room_num = True
                valid_booking = booking
                break

        if not is_valid_room_num or valid_booking is None:
            raise AppException(
                message="Invalid room number",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if request.type == ServiceType.FOOD and not valid_booking.food_req:
            valid_booking.food_req = True

        elif request.type == ServiceType.CLEANING and not valid_booking.clean_req:
            valid_booking.clean_req = True
        else:
            raise AppException(
                message="Service Request already exists",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        self.booking_repo.update_booking(valid_booking)

        type = request.type
        details = request.details
        booking_id = valid_booking.id
        created_at = datetime.now()

        service_request = self._create_service_request(
            room_num, type, details, user_id, booking_id, created_at
        )

        self.service_request_repo.save_service_request(service_request)

    def get_all_pending_service_requests(self) -> List[ServiceRequest]:
        return self.service_request_repo.get_all_pending_service_requests()

    def get_service_request_by_userID(self, current_user) -> List[ServiceRequest]:
        user_id = current_user.get("sub")
        return self.service_request_repo.get_pending_service_requests_by_user_id(
            user_id
        )

    def assign_service_request(
        self, service_request_id: str, request: assign_service_request_dto
    ) -> None:
        employee_id = request.employee_id
        _ = self.user_repo.get_user_by_id(employee_id)
        self.service_request_repo.assign_service_request(
            service_request_id, employee_id
        )

    def get_assigned_service_requests(
        self, current_user
    ) -> List[AssignedPendingServiceRequestDTO]:
        employee_id = current_user.get("sub")
        response: List[ServiceRequest] = (
            self.service_request_repo.get_assigned_service_requests(employee_id)
        )
        return [
            AssignedPendingServiceRequestDTO(
                service_request_id=resp.id,
                user_id=resp.user_id,
                room_num=resp.room_num,
                status=resp.status,
                type=resp.type,
                details=resp.details,
            )
            for resp in response
        ]

    def update_service_request(
        self, service_request_id: str, request: UpdateServiceRequestStatus
    ) -> None:
        req = self.service_request_repo.get_service_request_by_id(service_request_id)
        if req is None:
            raise AppException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Service request not found",
            )
        update_status = request.status
        if update_status != ServiceStatus.DONE:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid status",
            )
        self.service_request_repo.update_service_request(
            service_request_id, update_status
        )
        booking_id = req.booking_id
        booking = self.booking_repo.get_booking_by_ID(booking_id)
        if req.type == ServiceType.FOOD:
            booking.food_req = False
        else:
            booking.clean_req = False
        self.booking_repo.update_booking(booking)
