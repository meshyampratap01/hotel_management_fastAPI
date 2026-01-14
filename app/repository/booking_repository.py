from datetime import date
from typing import Any, Dict, List
from boto3.dynamodb.conditions import Attr, Key
from botocore.utils import ClientError
from fastapi import Depends, status
from app.app_exception.app_exception import AppException
from app.dependencies import get_ddb_resource, get_table_name
from app.models import bookings


class BookingRepository:
    def __init__(
        self, ddb_resource=Depends(get_ddb_resource), table_name=Depends(get_table_name)
    ):
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def save_booking(self, booking: bookings.Booking):
        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"User#{booking.user_id}",
                                "sk": f"booking#{booking.id}",
                                **booking.model_dump(mode="json"),
                            },
                            "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"Booking#{booking.id}",
                                "sk": "META",
                                **booking.model_dump(mode="json"),
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                ]
            )
        except ClientError as e:
            error = e.response.get("Error", {})
            code = error.get("Code")

            if code == "TransactionCanceledException":
                reasons = e.response.get("CancellationReasons", [])

                if any(r.get("Code") == "ConditionalCheckFailed" for r in reasons):
                    raise AppException(
                        status_code=status.HTTP_409_CONFLICT,
                        message="Booking already exists",
                    )

            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create booking",
            )

    def get_booking_by_ID(self, bookingID: str) -> bookings.Booking:
        pk = f"Booking#{bookingID}"
        sk = "META"

        try:
            response = self.table.get_item(
                Key={
                    "pk": pk,
                    "sk": sk,
                }
            )
        except ClientError:
            raise AppException(
                message="Failed to fetch booking by id",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        item = response.get("Item")
        if not item:
            raise AppException(
                message="No bookings found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return bookings.Booking(
            **item,
        )

    def update_booking(self, booking: bookings.Booking) -> None:
        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": f"User#{booking.user_id}",
                                "sk": f"booking#{booking.id}",
                            },
                            "UpdateExpression": """
                                SET
                                    #status = :status,
                                    check_in = :check_in,
                                    check_out = :check_out,
                                    food_req = :food_req,
                                    clean_req = :clean_req
                            """,
                            "ExpressionAttributeNames": {
                                "#status": "status",
                            },
                            "ExpressionAttributeValues": {
                                ":status": booking.status,
                                ":check_in": booking.check_in.isoformat(),
                                ":check_out": booking.check_out.isoformat(),
                                ":food_req": booking.food_req,
                                ":clean_req": booking.clean_req,
                            },
                            "ConditionExpression": "attribute_exists(pk)",
                        }
                    },
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": f"Booking#{booking.id}",
                                "sk": "META",
                            },
                            "UpdateExpression": """
                                SET
                                    #status = :status,
                                    check_in = :check_in,
                                    check_out = :check_out,
                                    food_req = :food_req,
                                    clean_req = :clean_req
                            """,
                            "ExpressionAttributeNames": {
                                "#status": "status",
                            },
                            "ExpressionAttributeValues": {
                                ":status": booking.status,
                                ":check_in": booking.check_in.isoformat(),
                                ":check_out": booking.check_out.isoformat(),
                                ":food_req": booking.food_req,
                                ":clean_req": booking.clean_req,
                            },
                            "ConditionExpression": "attribute_exists(pk)",
                        }
                    },
                ]
            )

        except ClientError as e:
            error = e.response.get("Error", {})
            code = error.get("Code")

            if code == "TransactionCanceledException":
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Booking not found",
                )

            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to update booking",
            )

    def get_bookings_by_userID(self, userID: str) -> List[bookings.Booking]:
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"User#{userID}") & Key("sk").begins_with("booking#")
                ),
                FilterExpression=Attr("status").eq("Booked"),
            )

        except ClientError:
            raise AppException(
                message="Failed to fetch bookings",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        items = response.get("Items", [])

        return [bookings.Booking(**item) for item in items]

    def scan_expired_bookings(self) -> List[Dict[str, Any]]:
        today = date.today().isoformat()

        response = self.ddb_client.scan(
            TableName=self.table_name,
            FilterExpression="#s = :booked AND check_out < :today",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":booked": bookings.BookingStatus.Booking_Status_Booked,
                ":today": today,
            },
        )
        return response.get("Items", [])

    def mark_booking_completed(self, booking_id: str, user_id: str):
        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": f"Booking#{booking_id}",
                                "sk": "META",
                            },
                            "UpdateExpression": "SET #s = :completed",
                            "ConditionExpression": "#s = :booked",
                            "ExpressionAttributeNames": {
                                "#s": "status",
                            },
                            "ExpressionAttributeValues": {
                                ":completed": bookings.BookingStatus.Booking_Status_Completed.value,
                                ":booked": bookings.BookingStatus.Booking_Status_Booked.value,
                            },
                        }
                    },
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": f"User#{user_id}",
                                "sk": f"booking#{booking_id}",
                            },
                            "UpdateExpression": "SET #s = :completed",
                            "ExpressionAttributeNames": {
                                "#s": "status",
                            },
                            "ExpressionAttributeValues": {
                                ":completed": bookings.BookingStatus.Booking_Status_Completed.value,
                            },
                        }
                    },
                ]
            )
        except ClientError as e:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to mark booking as completed: {e.response['Error']['Message']}",
            )
