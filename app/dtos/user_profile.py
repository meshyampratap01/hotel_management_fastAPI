from pydantic import BaseModel, EmailStr
from app.models.users import Role


class UserProfileDTO(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: Role
    available: bool
