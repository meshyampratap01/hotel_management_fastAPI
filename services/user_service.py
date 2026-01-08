import uuid
from datetime import datetime, timezone
from fastapi import status, Depends
from app_exception.app_exception import AppException
from models import users
from dtos.auth_requests import UserCreateRequest, UserLoginRequest
from utils import utils
from repository.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository = Depends(UserRepository)) -> None:
        self.user_repo = user_repo

    def _create_user(
        self,
        name: str,
        email: str,
        password: str,
        role: users.Role = users.Role.GUEST,
    ) -> users.User:
        return users.User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=utils.hash_password(password),
            role=role,
            available=False,
        )

    def signup(self, request: UserCreateRequest) -> None:
        email = request.email.lower()

        user = self._create_user(
            name=request.name,
            email=email,
            password=request.password,
        )

        try:
            self.user_repo.save_user(user)
        except AppException:
            raise
        except Exception:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create user",
            )

    def login(self, request: UserLoginRequest) -> str:
        email = request.email.lower()

        try:
            user: users.User = self.user_repo.get_user_by_email(email)
        except AppException:
            raise

        if not utils.verify_password(request.password, user.password):
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid email or password",
            )

        payload = {
            "sub": user.id,
            "user_name": user.name,
            "role": user.role,
            "iat": datetime.now(tz=timezone.utc),
        }

        try:
            return utils.generate_jwt(payload)
        except AppException:
            raise

    def get_profile(self, user_id: str) -> users.User:
        try:
            return self.user_repo.get_user_by_id(user_id)
        except AppException:
            raise
