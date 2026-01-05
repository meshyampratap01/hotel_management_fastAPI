from abc import ABC, abstractmethod
from boto3.dynamodb.conditions import Attr, Key
from botocore.utils import ClientError
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
    def get_room_by_number(self, room_number: int) -> rooms.Room | None:
        pass

    @abstractmethod
    def get_available_rooms(self) -> list[rooms.Room]:
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
                raise ValueError("Room already exists")
            raise e

    def get_room_by_number(self, room_number: int) -> rooms.Room | None:
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
            return None

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
                raise ValueError("Room not found")
            raise e

    def get_all_rooms(self):
        pk = "ROOMS"
        try:
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(pk) & Key("sk").begins_with("room#")
                )
            )
        except ClientError as e:
            raise e

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
        except ClientError as e:
            raise e

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
