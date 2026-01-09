from fastapi import APIRouter, Depends, status
from response.response import APIResponse
from dependencies import (
    require_roles,
)
from dtos.booking_requests import CreateBookingRequest
from models.users import Role
from services.booking_service import BookingService

booking_router = APIRouter(prefix="/bookings")


@booking_router.post(
    "/bookRoom", response_model=APIResponse, status_code=status.HTTP_201_CREATED
)
def book_room(
    create_booking_request: CreateBookingRequest,
    booking_service: BookingService = Depends(BookingService),
    current_user=Depends(require_roles((Role.GUEST.value))),
):
    booking = booking_service.book_room(create_booking_request, current_user)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="Room Booked Successfully",
        data=booking,
    )


@booking_router.delete(
    "/{booking_id}", status_code=status.HTTP_200_OK, response_model=APIResponse
)
def cancel_booking(
    booking_id: str,
    _=Depends(require_roles(Role.GUEST.value)),
    booking_service: BookingService = Depends(BookingService),
):
    booking_service.cancel_booking(booking_id)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Booking Cancelled Successfully",
    )


@booking_router.get("/", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_bookings(
    current_user=Depends(require_roles((Role.GUEST.value))),
    booking_service: BookingService = Depends(BookingService),
):
    bookings = booking_service.get_active_bookings_by_user(current_user.get("sub"))
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Bookings Fetched Successfully",
        data=bookings,
    )
