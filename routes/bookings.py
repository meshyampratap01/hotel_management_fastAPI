from fastapi import APIRouter, Depends, HTTPException, status
from app_exception.app_exception import AppException
from dependencies import (
    get_booking_service,
    require_roles,
)
from dtos.booking_requests import CreateBookingRequest
from models.roles import Role
from models.bookings import Booking
from services.booking_service import BookingService

booking_router = APIRouter(prefix="/bookings")


@booking_router.post(
    "/bookRoom", response_model=Booking, status_code=status.HTTP_201_CREATED
)
def book_room(
    create_booking_request: CreateBookingRequest,
    booking_service=Depends(get_booking_service),
    current_user=Depends(require_roles((Role.GUEST.value))),
):
    try:
        return booking_service.book_room(create_booking_request, current_user)
    except HTTPException:
        raise


@booking_router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def cancel_booking(
    booking_id: str,
    _=Depends(require_roles(Role.GUEST.value)),
    booking_service: BookingService = Depends(get_booking_service),
):
    try:
        booking_service.cancel_booking(booking_id)
        return {"detail": "booking successfully cancelled"}
    except AppException:
        raise


@booking_router.get("/", response_model=list[Booking], status_code=status.HTTP_200_OK)
def get_bookings(
    current_user=Depends(require_roles((Role.GUEST.value))),
    booking_service: BookingService = Depends(get_booking_service),
):
    try:
        bookings = booking_service.get_active_bookings_by_user(
            current_user.get("sub"))
        return bookings
    except Exception:
        raise
