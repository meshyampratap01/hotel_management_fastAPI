from abc import ABC, abstractmethod
from botocore.utils import ClientError
from datetime import datetime
from fastapi import HTTPException, status
from models import bookings


class BookingRepository(ABC):
    @abstractmethod
    def get_all_bookings(self):
        pass

    @abstractmethod
    def save_booking(self, booking: bookings.Booking):
        pass

    @abstractmethod
    def get_booking_by_userID(self, userID: str):
        pass

    @abstractmethod
    def get_booking_by_ID(self, bookingID: str):
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
            print(e.response)
            error = e.response.get("Error", {})
            code = error.get("Code")

            if code == "TransactionCanceledException":
                reasons = e.response.get("CancellationReasons", [])

                if any(r.get("Code") == "ConditionalCheckFailed" for r in reasons):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Booking already exists",
                    )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create booking",
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
        except ClientError as e:
            raise e

        item = response.get("Item")
        if not item:
            return None

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
            print(e.response)
            error = e.response.get("Error", {})
            code = error.get("Code")

            if code == "TransactionCanceledException":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update booking",
            )

    def get_booking_by_userID(self, userID: str):
        pass

    def get_expired_bookings(self):
        pass
