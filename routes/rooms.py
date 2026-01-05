from fastapi import APIRouter, Depends, status
from app_exception.app_exception import AppException
from dependencies import get_booking_repository, get_room_repository, require_roles
from dtos.room_requests import AddRoomRequest, UpdateRoomRequest
from models import rooms
from models import roles
from models.roles import Role
from services import room_service

room_router = APIRouter(prefix="/rooms")


@room_router.get("/", status_code=status.HTTP_200_OK)
def get_rooms_by_role(
    room_repo=Depends(get_room_repository),
    current_user=Depends(require_roles(Role.GUEST.value, Role.MANAGER.value)),
):
    role = current_user.get("role")
    print(role)
    print(Role.GUEST.value)
    print(Role.MANAGER.value)
    try:
        if role == Role.MANAGER.value:
            print("hello manager")
            return room_service.get_all_rooms(room_repo)
        elif role == Role.GUEST.value:
            print("hello guest")
            return room_service.get_available_rooms(room_repo)
    except AppException:
        raise


@room_router.post("/", status_code=status.HTTP_201_CREATED, response_model=rooms.Room)
def add_room(
    add_room_request: AddRoomRequest,
    _=Depends(require_roles(roles.Role.MANAGER)),
    room_repo=Depends(get_room_repository),
):
    try:
        return room_service.add_room(add_room_request, room_repo)
    except AppException:
        raise


@room_router.delete("/{room_num}")
def delete_room(
    room_num: int,
    _=Depends(require_roles("Manager")),
    room_repo=Depends(get_room_repository),
):
    try:
        room_service.delete_room(room_num, room_repo)
        return {"detail": "room deleted successfully"}
    except AppException:
        raise


@room_router.patch("/{room_num}")
def update_room(
    update_room_request: UpdateRoomRequest,
    room_num: int,
    _=Depends(require_roles("Manager")),
    room_repo=Depends(get_room_repository),
):
    try:
        room_service.update_room(room_num, update_room_request, room_repo)
        return {"detail": "Room updated successfully"}
    except AppException:
        raise
