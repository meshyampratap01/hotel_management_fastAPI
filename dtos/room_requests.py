from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from models.rooms import RoomType


class AddRoomRequest(BaseModel):
    number: Annotated[int, Field(gt=0, description="Room number must be positive")]
    type: RoomType
    price: Annotated[int, Field(gt=0, description="Room price must be greater than 0")]
    description: Annotated[str, Field(min_length=1, description="Room description")]


class UpdateRoomRequest(BaseModel):
    type: Optional[RoomType] = None
    price: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None
    description: Optional[str] = None
