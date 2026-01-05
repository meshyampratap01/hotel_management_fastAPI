import uuid

from botocore.utils import ClientError
from fastapi import status
from app_exception.app_exception import AppException
from dtos.room_requests import AddRoomRequest, UpdateRoomRequest
from models import rooms


def get_all_rooms(room_repo) -> list[rooms.Room]:
    try:
        rooms = room_repo.get_all_rooms()
        return rooms
    except AppException:
        raise


def get_available_rooms(room_repo) -> list[rooms.Room]:
    try:
        rooms = room_repo.get_available_rooms()
        return rooms
    except AppException:
        raise


def add_room(add_room_request: AddRoomRequest, room_repo):
    room_num = add_room_request.number
    room_type = add_room_request.type
    room_price = add_room_request.price
    room_description = add_room_request.description

    new_room = rooms.Room(
        id=str(uuid.uuid4()),
        number=room_num,
        type=room_type,
        price=room_price,
        is_available=True,
        description=room_description,
    )

    try:
        room_repo.add_room(new_room)
        return new_room
    except AppException:
        raise


def delete_room(room_num: int, room_repo):
    try:
        room = room_repo.get_room_by_number(room_num)
        if room.is_available is True:
            room_repo.delete_room(room_num)
        else:
            raise AppException(
                message="room is booked and can not be deleted",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    except AppException:
        raise


def update_room(room_num: int, data: UpdateRoomRequest, room_repo):
    fields = {}
    if data.type is not None:
        fields["room_type"] = data.type

    if data.price is not None:
        fields["price"] = data.price

    if data.is_available is not None:
        fields["is_available"] = data.is_available

    if data.description is not None:
        fields["description"] = data.description

    if not fields:
        raise AppException(
            message="No fields provided for update",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        room_repo.update_room(room_num, fields)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise AppException(
                message="Room not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        raise AppException(
            message="Failed to update room",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
