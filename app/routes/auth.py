from fastapi import APIRouter, Depends
from response.response import APIResponse
from dtos.auth_requests import UserCreateRequest, UserLoginRequest
from services.user_service import UserService
from starlette import status

auth_router = APIRouter(prefix="/auth")


@auth_router.post(
    "/signup", status_code=status.HTTP_201_CREATED, response_model=APIResponse
)
def sign_up(user_request: UserCreateRequest, user_service=Depends(UserService)):
    user_service.signup(request=user_request)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="User created successfully",
    )


@auth_router.post("/login", status_code=status.HTTP_200_OK, response_model=APIResponse)
def login(login_request: UserLoginRequest, user_service=Depends(UserService)):
    try:
        token = user_service.login(request=login_request)
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="User logged in successfully",
            data={"token": token},
        )
    except Exception:
        raise
