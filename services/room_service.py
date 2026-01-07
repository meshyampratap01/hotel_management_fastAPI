import uuid
from typing import List
from botocore.utils import ClientError
from fastapi import status
from app_exception.app_exception import AppException
from dtos.room_requests import AddRoomRequest, UpdateRoomRequest
from models import rooms
from repository.room_repository import RoomRepository


class RoomService:
    def __init__(self, room_repo: RoomRepository):
        self.room_repo = room_repo

    def get_all_rooms(self) -> List[rooms.Room]:
        try:
            return self.room_repo.get_all_rooms()
        except AppException:
            raise

    def get_available_rooms(self) -> List[rooms.Room]:
        try:
            return self.room_repo.get_available_rooms()
        except AppException:
            raise

    def add_room(self, request: AddRoomRequest) -> rooms.Room:
        new_room = rooms.Room(
            id=str(uuid.uuid4()),
            number=request.number,
            type=request.type,
            price=request.price,
            is_available=True,
            description=request.description,
        )

        try:
            self.room_repo.add_room(new_room)
            return new_room
        except AppException:
            raise

    def delete_room(self, room_num: int) -> None:
        try:
            room: rooms.Room = self.room_repo.get_room_by_number(room_num)

            if not room.is_available:
                raise AppException(
                    message="Room is booked and cannot be deleted",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            self.room_repo.delete_room(room_num)

        except AppException:
            raise

    def update_room(self, room_num: int, data: UpdateRoomRequest) -> None:
        update_fields = {}

        if data.type is not None:
            update_fields["room_type"] = data.type

        if data.price is not None:
            update_fields["price"] = data.price

        if data.is_available is not None:
            update_fields["is_available"] = data.is_available

        if data.description is not None:
            update_fields["description"] = data.description

        if not update_fields:
            raise AppException(
                message="No fields provided for update",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self.room_repo.update_room(room_num, update_fields)

        except AppException:
            raise AppException(
                message="Failed to update room",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
