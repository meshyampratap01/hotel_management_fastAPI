from contextlib import asynccontextmanager
from fastapi import FastAPI
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
app.include_router(auth.auth_router)
app.include_router(bookings.booking_router)
app.include_router(rooms.room_router)
