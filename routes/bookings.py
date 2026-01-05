from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_booking_repository, get_room_repository, get_current_user
from dtos.booking_requests import CreateBookingRequest
from services import booking_service
from models.bookings import Booking

booking_router = APIRouter(prefix="/bookings")


@booking_router.post("/bookRoom", response_model=Booking)
def book_room(
    create_booking_request: CreateBookingRequest,
    booking_repo=Depends(get_booking_repository),
    room_repo=Depends(get_room_repository),
    current_user=Depends(get_current_user),
):
    try:
        return booking_service.BookRoom(
            create_booking_request, booking_repo, room_repo, current_user
        )
    except HTTPException:
        raise


@booking_router.delete("/{booking_id}", response_model=Booking)
def cancel_booking(
    booking_id: str,
    _=Depends(get_current_user),
    booking_repo=Depends(get_booking_repository),
    room_repo=Depends(get_room_repository),
):
    try:
        return booking_service.cancel_booking(
            bookingID=booking_id, booking_repo=booking_repo, room_repo=room_repo
        )
    except Exception:
        raise
