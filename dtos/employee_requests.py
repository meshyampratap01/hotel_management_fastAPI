from pydantic import BaseModel, EmailStr, Field
from models.users import Role


class CreateEmployeeRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Employee full name")
    email: EmailStr = Field(..., description="Employee email address")
    password: str = Field(..., min_length=8, description="Employee password")
    role: Role = Field(..., min_length=1, description="Employee role")
    available: bool = Field(..., description="Employee availability status")


class UpdateEmployeeRequest(BaseModel):
    available: bool = Field(..., description="Employee availability status")
