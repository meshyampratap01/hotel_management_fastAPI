from typing import Any, Dict, List
import boto3

from letstayinn_package.booking_repository import BookingRepository
from mypy_boto3_dynamodb import ServiceResource


def getddbresource() -> ServiceResource:
    return boto3.resource("dynamodb", region_name="ap-south-1")


def lambda_handler(event, context):
    ddb_resource: ServiceResource = getddbresource()
    booking_repository: BookingRepository = BookingRepository(
        "letstayinn_fastapi", ddb_resource=ddb_resource
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
