from pydantic import BaseModel, EmailStr
from models.roles import Role


class UserProfileDTO(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    available: bool
