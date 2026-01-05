from typing import Callable
from fastapi import HTTPException, Request, status
from repository.user_repository import UserRepository
from repository.booking_repository import BookingRepository
from utils import utils
from repository.room_repository import RoomRepository


def get_user_repository(req: Request) -> UserRepository:
    return req.app.state.user_repo


def get_booking_repository(req: Request) -> BookingRepository:
    return req.app.state.booking_repo


def get_room_repository(req: Request) -> RoomRepository:
    return req.app.state.room_repo


def get_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return auth.split(" ")[1]


def require_roles(*allowed_roles: str) -> Callable:
    def role_checker(request: Request):
        token = get_token(request)

        try:
            payload = utils.verify_jwt(token)
        except HTTPException:
            raise

        user_role = payload.get("role")

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User unauthorized"
            )

        return payload

    return role_checker
