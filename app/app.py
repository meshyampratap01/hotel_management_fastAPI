from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.app_exception.app_exception import AppException
from app.routes import (
    auth,
    bookings,
    employees,
    feedbacks,
    profile,
    rooms,
    service_request,
)
from app.dependencies import lifespan
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(auth.auth_router)
app.include_router(employees.employee_router)
app.include_router(service_request.service_request_router)
app.include_router(feedbacks.router)
app.include_router(bookings.booking_router)
app.include_router(rooms.room_router)
app.include_router(profile.router)
