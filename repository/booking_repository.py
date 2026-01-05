from abc import ABC, abstractmethod
from boto3.dynamodb.conditions import Attr, Key
from botocore.utils import ClientError
from datetime import datetime
from fastapi import HTTPException, status
from app_exception.app_exception import AppException
from models import bookings


class BookingRepository(ABC):
    @abstractmethod
    def get_all_bookings(self):
        pass

    @abstractmethod
    def save_booking(self, booking: bookings.Booking):
        pass

    @abstractmethod
    def get_bookings_by_userID(self, userID: str) -> list[bookings.Booking]:
        pass

    @abstractmethod
    def update_booking(self, booking: bookings.Booking):
        pass

    @abstractmethod
    def get_expired_bookings(self):
        pass


class DDBBookingRepository(BookingRepository):
    def __init__(self, ddb_resource, table_name: str):
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def get_all_bookings(self):
        pass

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
                                "booking_id": booking.id,
                                "room_id": booking.room_id,
                                "room_num": booking.room_num,
                                "check_in": booking.check_in.isoformat(),
                                "check_out": booking.check_out.isoformat(),
                                "status": booking.status,
                                "food_req": booking.food_req,
                                "clean_req": booking.clean_req,
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
                                "id": booking.id,
                                "user_id": booking.user_id,
                                "room_id": booking.room_id,
                                "room_num": booking.room_num,
                                "check_in": booking.check_in.isoformat(),
                                "check_out": booking.check_out.isoformat(),
                                "status": booking.status,
                                "food_req": booking.food_req,
                                "clean_req": booking.clean_req,
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

    def get_booking_by_ID(self, bookingID: str):
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
            id=item["id"],
            user_id=item["user_id"],
            room_id=item["room_id"],
            room_num=item["room_num"],
            check_in=datetime.fromisoformat(item["check_in"]),
            check_out=datetime.fromisoformat(item["check_out"]),
            status=item["status"],
            food_req=item["food_req"],
            clean_req=item["clean_req"],
        )

    def update_booking(self, booking: bookings.Booking):
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

    def get_bookings_by_userID(self, userID: str):
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"User#{userID}") & Key(
                        "sk").begins_with("booking#")
                ),
                FilterExpression=Attr("status").eq("Booked"),
            )

        except ClientError:
            raise AppException(
                message="Failed to fetch bookings",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        items = response.get("Items", [])

        return [
            bookings.Booking(
                id=item["booking_id"],
                user_id=userID,
                room_id=item["room_id"],
                room_num=item["room_num"],
                check_in=datetime.fromisoformat(item["check_in"]),
                check_out=datetime.fromisoformat(item["check_out"]),
                status=item["status"],
                food_req=item["food_req"],
                clean_req=item["clean_req"],
            )
            for item in items
        ]

    def get_expired_bookings(self):
        pass
