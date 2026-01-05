from fastapi import HTTPException, Request
from repository.user_repository import UserRepository
from repository.booking_repository import BookingRepository
from repository.room_repository import RoomRepository
from utils import utils


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


def get_current_user(request: Request):
    token = get_token(request)
    try:
        payload = utils.verify_jwt(token)
        return payload
    except HTTPException:
        raise
