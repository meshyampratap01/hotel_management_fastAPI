from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from models import room_types


class AddRoomRequest(BaseModel):
    number: Annotated[int, Field(
        gt=0, description="Room number must be positive")]
    type: room_types.RoomType
    price: Annotated[int, Field(
        gt=0, description="Room price must be greater than 0")]
    description: Annotated[str, Field(
        min_length=1, description="Room description")]


class UpdateRoomRequest(BaseModel):
    type: Optional[room_types.RoomType] = None
    price: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None
    description: Optional[str] = None
