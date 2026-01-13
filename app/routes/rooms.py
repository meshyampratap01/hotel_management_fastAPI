from fastapi import APIRouter, Depends, status
from app.response.response import APIResponse
from app.dependencies import (
    require_roles,
)
from app.dtos.room_requests import AddRoomRequest, UpdateRoomRequest
from app.models.users import Role
from app.services.room_service import RoomService

room_router = APIRouter(prefix="/rooms")


@room_router.get("", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_rooms_by_role(
    room_service: RoomService = Depends(RoomService),
    current_user=Depends(require_roles(Role.GUEST.value, Role.MANAGER.value)),
):
    role = current_user.get("role")
    if role == Role.MANAGER.value:
        rooms = room_service.get_all_rooms()
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="Rooms Fetched Successfully",
            data=rooms,
        )
    elif role == Role.GUEST.value:
        rooms = room_service.get_available_rooms()
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="Rooms Fetched Successfully",
            data=rooms,
        )


@room_router.post("", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def add_room(
    add_room_request: AddRoomRequest,
    _=Depends(require_roles(Role.MANAGER)),
    room_service: RoomService = Depends(RoomService),
):
    room = room_service.add_room(add_room_request)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="Room added successfully",
        data=room,
    )


@room_router.delete(
    "/{room_num}", status_code=status.HTTP_200_OK, response_model=APIResponse
)
def delete_room(
    room_num: int,
    _=Depends(require_roles("Manager")),
    room_service=Depends(RoomService),
):
    room_service.delete_room(room_num)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Room deleted successfully",
    )


@room_router.patch(
    "/{room_num}", status_code=status.HTTP_200_OK, response_model=APIResponse
)
def update_room(
    update_room_request: UpdateRoomRequest,
    room_num: int,
    _=Depends(require_roles("Manager")),
    room_service=Depends(RoomService),
):
    room_service.update_room(room_num, update_room_request)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Room updated successfully",
    )
