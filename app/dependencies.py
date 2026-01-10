from contextlib import asynccontextmanager
import os
from typing import Callable

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status

from app.utils import jwt


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    ddb_resource = boto3.resource("dynamodb")
    app.state.ddb_resource = ddb_resource
    app.state.table_name = str(os.getenv("table_name"))
    yield


def get_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return auth.split(" ")[1]


def require_roles(*allowed_roles: str) -> Callable:
    def role_checker(request: Request):
        token = get_token(request)

        try:
            payload = jwt.verify_jwt(token)
        except HTTPException:
            raise

        user_role = payload.get("role")

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User unauthorized"
            )

        return payload

    return role_checker


def get_ddb_resource(req: Request):
    return req.app.state.ddb_resource


def get_table_name(req: Request):
    return req.app.state.table_name
