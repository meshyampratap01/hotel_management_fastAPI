from fastapi import APIRouter, Depends, status
from app_exception.app_exception import AppException
from dependencies import (
    require_roles,
)
from dtos.room_requests import AddRoomRequest, UpdateRoomRequest
from models import rooms
from models.users import Role
from services.room_service import RoomService

room_router = APIRouter(prefix="/rooms")


@room_router.get("/", status_code=status.HTTP_200_OK)
def get_rooms_by_role(
    room_service: RoomService = Depends(RoomService),
    current_user=Depends(require_roles(Role.GUEST.value, Role.MANAGER.value)),
):
    role = current_user.get("role")
    print(role)
    print(Role.GUEST.value)
    print(Role.MANAGER.value)
    try:
        if role == Role.MANAGER.value:
            print("hello manager")
            return room_service.get_all_rooms()
        elif role == Role.GUEST.value:
            print("hello guest")
            return room_service.get_available_rooms()
    except AppException:
        raise


@room_router.post("/", status_code=status.HTTP_201_CREATED, response_model=rooms.Room)
def add_room(
    add_room_request: AddRoomRequest,
    _=Depends(require_roles(Role.MANAGER)),
    room_service=Depends(RoomService),
):
    try:
        return room_service.add_room(add_room_request)
    except AppException:
        raise


@room_router.delete("/{room_num}")
def delete_room(
    room_num: int,
    _=Depends(require_roles("Manager")),
    room_service=Depends(RoomService),
):
    try:
        room_service.delete_room(room_num)
        return {"detail": "room deleted successfully"}
    except AppException:
        raise


@room_router.patch("/{room_num}")
def update_room(
    update_room_request: UpdateRoomRequest,
    room_num: int,
    _=Depends(require_roles("Manager")),
    room_service=Depends(RoomService),
):
    try:
        room_service.update_room(room_num, update_room_request)
        return {"detail": "Room updated successfully"}
    except AppException:
        raise
