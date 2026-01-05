import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from models import users, roles
from dtos.auth_requests import UserCreateRequest, UserLoginRequest
from utils import utils


def create_user(
    name: str,
    email: str,
    password: str,
    role=roles.Role.GUEST.value,
) -> users.User:
    return users.User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        password=utils.hash_password(password),
        role=role,
        available=False,
    )


def signup(request: UserCreateRequest, userRepo):
    name = request.name
    email = request.email.lower()
    password = request.password
    new_user = create_user(name, email, password)

    try:
        userRepo.save_user(new_user)
    except HTTPException:
        raise


def login(request: UserLoginRequest, userRepo):
    email = request.email.lower()
    password = request.password
    user = userRepo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    if not utils.verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    payload = {
        "sub": user.id,
        "user_name": user.name,
        "role": user.role,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=60),
    }

    try:
        token = utils.generate_jwt(payload)
        return token
    except Exception:
        raise
