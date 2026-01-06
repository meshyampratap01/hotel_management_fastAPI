from abc import ABC, abstractmethod
from boto3.dynamodb.conditions import Attr, Key
from botocore.utils import ClientError
from fastapi import status
from app_exception.app_exception import AppException
from models import rooms


class RoomRepository(ABC):
    @abstractmethod
    def add_room(self, room: rooms.Room):
        pass

    @abstractmethod
    def update_room_availability(self, room_num: int, is_available: bool):
        pass

    @abstractmethod
    def get_all_rooms(self) -> list[rooms.Room]:
        pass

    @abstractmethod
    def get_room_by_number(self, room_number: int) -> rooms.Room:
        pass

    @abstractmethod
    def get_available_rooms(self) -> list[rooms.Room]:
        pass

    @abstractmethod
    def delete_room(self, room_num: int):
        pass

    @abstractmethod
    def update_room(self, room_num: int, fields: dict):
        pass


class DDBRoomRepository(RoomRepository):
    def __init__(self, ddb_resource, table_name) -> None:
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def add_room(self, room: rooms.Room):
        pk = "ROOMS"
        sk = f"room#{room.number}"

        try:
            self.table.put_item(
                Item={
                    "pk": pk,
                    "sk": sk,
                    "id": room.id,
                    "number": room.number,
                    "room_type": room.type,
                    "price": room.price,
                    "is_available": room.is_available,
                    "description": room.description,
                },
                ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise AppException(
                    message="Room already exists", status_code=status.HTTP_409_CONFLICT
                )
            raise AppException(
                message="Failed to create room",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_room_by_number(self, room_number: int) -> rooms.Room:
        pk = "ROOMS"
        sk = f"room#{room_number}"

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
            raise AppException(
                message="Room not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return rooms.Room(
            id=item["pk"],
            number=item["number"],
            type=item["room_type"],
            price=item["price"],
            is_available=item["is_available"],
            description=item.get("description", ""),
        )

    def update_room_availability(self, room_num: int, is_available: bool):
        pk = "ROOMS"
        sk = f"room#{room_num}"

        try:
            self.table.update_item(
                Key={
                    "pk": pk,
                    "sk": sk,
                },
                UpdateExpression="SET is_available = :available",
                ExpressionAttributeValues={
                    ":available": is_available,
                },
                ConditionExpression="attribute_exists(pk)",
                ReturnValues="UPDATED_NEW",
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise AppException(
                    message="Room not found", status_code=status.HTTP_409_CONFLICT
                )
            raise AppException(
                message="Failed to update room availability",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_all_rooms(self):
        pk = "ROOMS"
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(pk) & Key("sk").begins_with("room#")
                )
            )
        except ClientError:
            raise AppException(
                message="Failed to fetch rooms",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        items = response.get("Items", [])

        return [
            rooms.Room(
                id=item["pk"],
                number=item["number"],
                type=item["room_type"],
                price=item["price"],
                is_available=item["is_available"],
                description=item["description"],
            )
            for item in items
        ]

    def get_available_rooms(self):
        pk = "ROOMS"
        rooms_list = []

        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(pk) & Key("sk").begins_with("room#")
                ),
                FilterExpression=Attr("is_available").eq(True),
            )
        except ClientError:
            raise AppException(
                message="Failed to fetch available rooms",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        items = response.get("Items", [])

        for item in items:
            rooms_list.append(
                rooms.Room(
                    id=item["pk"],
                    number=item["number"],
                    type=item["room_type"],
                    price=item["price"],
                    is_available=item["is_available"],
                    description=item.get("description", ""),
                )
            )

        return rooms_list

    def delete_room(self, room_num: int):
        pk = "ROOMS"
        sk = f"room#{room_num}"

        try:
            self.table.delete_item(
                Key={
                    "pk": pk,
                    "sk": sk,
                },
                ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
            )

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise AppException(
                    message="Room not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            raise AppException(
                message="Failed to delete room",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update_room(self, room_num: int, fields: dict):
        pk = "ROOMS"
        sk = f"room#{room_num}"

        update_expr = []
        expr_values = {}

        for key, value in fields.items():
            update_expr.append(f"{key} = :{key}")
            expr_values[f":{key}"] = value

        try:
            self.table.update_item(
                Key={"pk": pk, "sk": sk},
                UpdateExpression="SET " + ", ".join(update_expr),
                ExpressionAttributeValues=expr_values,
                ConditionExpression="attribute_exists(pk)",
            )
        except ClientError as e:
            raise e
