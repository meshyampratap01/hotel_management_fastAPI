from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_user_service
from dtos.auth_requests import UserCreateRequest, UserLoginRequest
from starlette import status

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
def sign_up(user_request: UserCreateRequest, user_service=Depends(get_user_service)):
    try:
        user_service.signup(request=user_request)
        return {"detail": "User successfully created, please login to continue"}
    except HTTPException:
        raise


@auth_router.post("/login", status_code=status.HTTP_200_OK)
def login(login_request: UserLoginRequest, user_service=Depends(get_user_service)):
    try:
        token = user_service.login(request=login_request)
        return {"token": token}
    except Exception:
        raise
