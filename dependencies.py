import os
from typing import Callable
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from repository.employee_repository import DDBEmployeeRepository
from repository.user_repository import DDBUserRepository
from repository.booking_repository import DDBBookingRepository
from services.booking_service import BookingService
from services.employee_service import EmployeeService
from services.room_service import RoomService
from services.user_service import UserService
from utils import utils
from repository.room_repository import DDBRoomRepository

load_dotenv()
table_name = str(os.getenv("table_name"))


def get_ddb_resource(req: Request):
    return req.app.state.ddb_resource


def get_user_service(ddb_resource=Depends(get_ddb_resource)) -> UserService:
    user_repo = DDBUserRepository(ddb_resource, table_name=table_name)
    return UserService(user_repo=user_repo)


def get_room_service(ddb_resource=Depends(get_ddb_resource)) -> RoomService:
    room_repo = DDBRoomRepository(ddb_resource, table_name)
    return RoomService(room_repo)


def get_booking_service(ddb_resource=Depends(get_ddb_resource)) -> BookingService:
    booking_repo = DDBBookingRepository(ddb_resource, table_name)
    room_repo = DDBRoomRepository(ddb_resource, table_name)
    return BookingService(booking_repo, room_repo)


def get_employee_service(ddb_resource=Depends(get_ddb_resource)) -> EmployeeService:
    employee_repo = DDBEmployeeRepository(ddb_resource, table_name)
    return EmployeeService(employee_repo)


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
