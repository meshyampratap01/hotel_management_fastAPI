from typing import Any, Dict, List
import boto3

from app.repository.booking_repository import BookingRepository


def getddbresource():
    return boto3.resource("dynamodb")


def lambda_handler(event, context):
    ddb_resource = getddbresource()
    booking_repository: BookingRepository = BookingRepository(
        ddb_resource, "letstayinn_fastapi"
    )

    expired_bookings: List[Dict[str, Any]] = booking_repository.scan_expired_bookings()

    for booking in expired_bookings:
        booking_id = booking.get("id")
        user_id = booking.get("user_id")
        booking_repository.mark_booking_completed(str(booking_id), str(user_id))

    return {
        "statusCode": 200,
        "body": "Success in updating completed bookings",
    }
