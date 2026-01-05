from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import (
    get_booking_repository,
    require_roles,
    get_room_repository,
)
from dtos.booking_requests import CreateBookingRequest
from models.roles import Role
from services import booking_service
from models.bookings import Booking

booking_router = APIRouter(prefix="/bookings")


@booking_router.post(
    "/bookRoom", response_model=Booking, status_code=status.HTTP_201_CREATED
)
def book_room(
    create_booking_request: CreateBookingRequest,
    booking_repo=Depends(get_booking_repository),
    room_repo=Depends(get_room_repository),
    current_user=Depends(require_roles((Role.GUEST.value))),
):
    try:
        return booking_service.BookRoom(
            create_booking_request, booking_repo, room_repo, current_user
        )
    except HTTPException:
        raise


@booking_router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def cancel_booking(
    booking_id: str,
    _=Depends(require_roles(Role.GUEST.value)),
    booking_repo=Depends(get_booking_repository),
    room_repo=Depends(get_room_repository),
):
    try:
        booking_service.cancel_booking(
            bookingID=booking_id, booking_repo=booking_repo, room_repo=room_repo
        )
        return {"detail": "booking successfully cancelled"}
    except Exception:
        raise


@booking_router.get("/", response_model=list[Booking], status_code=status.HTTP_200_OK)
def get_bookings(
    current_user=Depends(require_roles((Role.GUEST.value))),
    booking_repo=Depends(get_booking_repository),
):
    try:
        bookings = booking_service.get_active_bookings_by_userID(
            current_user.get("sub"), booking_repo=booking_repo
        )
        return bookings
    except Exception:
        raise
