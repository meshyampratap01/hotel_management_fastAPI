from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_user_repository
from services import user_service
from dtos.auth_requests import UserCreateRequest, UserLoginRequest
from starlette import status

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
def sign_up(user_request: UserCreateRequest, user_repo=Depends(get_user_repository)):
    try:
        user_service.signup(request=user_request, userRepo=user_repo)
        return {"detail": "User successfully created, please login to continue"}
    except HTTPException:
        raise


@auth_router.post("/login", status_code=status.HTTP_200_OK)
def login(login_request: UserLoginRequest, user_repo=Depends(get_user_repository)):
    try:
        token = user_service.login(request=login_request, userRepo=user_repo)
        return {"token": token}
    except Exception:
        raise
