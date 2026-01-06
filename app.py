from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app_exception.app_exception import AppException
from routes import auth, bookings, employees, rooms
import boto3


@asynccontextmanager
async def lifespan(app: FastAPI):
    ddb_resource = boto3.resource("dynamodb")
    app.state.ddb_resource = ddb_resource
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
app.include_router(employees.employee_router)
