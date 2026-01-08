from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class Role(str, Enum):
    GUEST = "Guest"
    KITCHEN_STAFF = "KitchenStaff"
    CLEANING_STAFF = "CleaningStaff"
    MANAGER = "Manager"


class User(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str
    role: Role
    available: bool

    model_config = ConfigDict(extra="ignore")
