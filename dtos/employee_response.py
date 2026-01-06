from pydantic import BaseModel
from models import roles


class EmployeeResponse(BaseModel):
    id: str
    name: str
    email: str
    role: roles.Role | str
    available: bool
