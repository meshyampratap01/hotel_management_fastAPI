from fastapi import APIRouter, Depends, status

from dependencies import get_room_repository, require_roles
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
    except Exception:
        raise
