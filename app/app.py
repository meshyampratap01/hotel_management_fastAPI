from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from app_exception.app_exception import AppException
from routes import auth, bookings, employees, feedbacks, profile, rooms, service_request
from dependencies import lifespan


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
async def validation_exception_handler(request, exc: RequestValidationError):
    message = "Validation errors:"
    for error in exc.errors():
        message += f"\nField: {error['loc']}, Error: {error['msg']}"
    return PlainTextResponse(message, status_code=400)


app.include_router(auth.auth_router)
app.include_router(bookings.booking_router)
app.include_router(rooms.room_router)
app.include_router(employees.employee_router)
app.include_router(service_request.service_request_router)
app.include_router(feedbacks.router)
app.include_router(profile.router)
