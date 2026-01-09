import bcrypt
import os
from fastapi import status
import jwt
from dotenv import load_dotenv

from app_exception.app_exception import AppException


load_dotenv()
my_secret_key = str(os.getenv("my_secret_key"))


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def generate_jwt(payload):
    try:
        token = jwt.encode(payload=payload, key=my_secret_key, algorithm="HS256")
        return token
    except Exception:
        raise AppException(
            message="Failed to generate jwt token",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def verify_jwt(token: str):
    try:
        return jwt.decode(
            token,
            key=my_secret_key,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise AppException(status_code=401, message="Token expired")
    except jwt.InvalidTokenError:
        raise AppException(status_code=401, message="Invalid token")
