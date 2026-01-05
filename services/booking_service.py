import uuid
from models.bookings import Booking
from models.booking_status import BookingStatus
from fastapi import HTTPException, status
from dtos.booking_requests import CreateBookingRequest


def BookRoom(
    create_booking_request: CreateBookingRequest, booking_repo, room_repo, current_user
):
    room_number = create_booking_request.room_number
    check_in_date = create_booking_request.check_in_date
    check_out_date = create_booking_request.check_out_date

    room = room_repo.get_room_by_number(room_number)
    if room is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="room not available"
        )

    if room.is_available is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="room already booked"
        )

    user_id = current_user.get("sub")

    new_booking = Booking(
        id=str(uuid.uuid4()),
        user_id=user_id,
        room_id=room.id,
        room_num=room_number,
        check_in=check_in_date,
        check_out=check_out_date,
        status=BookingStatus.Booking_Status_Booked.value,
        food_req=False,
        clean_req=False,
    )

    try:
        room_repo.update_room_availability(new_booking.room_num, False)
        booking_repo.save_booking(new_booking)
        return new_booking
    except HTTPException:
        raise


def cancel_booking(bookingID: str, booking_repo, room_repo):
    booking = booking_repo.get_booking_by_ID(bookingID)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no booking found for this booking id",
        )

    booking.status = BookingStatus.Booking_Status_Cancelled.value

    try:
        room_repo.update_room_availability(booking.room_num, True)
        booking_repo.update_booking(booking)
        return booking
    except Exception:
        raise
