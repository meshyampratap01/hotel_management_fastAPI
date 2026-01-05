from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app_exception.app_exception import AppException
from repository.user_repository import DDBUserRepository
from repository.booking_repository import DDBBookingRepository
from repository.room_repository import DDBRoomRepository
from routes import auth, bookings, rooms
import boto3


@asynccontextmanager
async def lifespan(app: FastAPI):
    ddb = boto3.resource("dynamodb")
    table_name = "letstayinn"
    app.state.user_repo = DDBUserRepository(
        ddb_resource=ddb, table_name=table_name)
    app.state.booking_repo = DDBBookingRepository(
        ddb_resource=ddb, table_name=table_name
    )
    app.state.room_repo = DDBRoomRepository(
        ddb_resource=ddb, table_name=table_name)
    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


app.include_router(auth.auth_router)
app.include_router(bookings.booking_router)
app.include_router(rooms.room_router)
