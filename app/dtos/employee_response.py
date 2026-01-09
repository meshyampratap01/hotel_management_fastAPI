from pydantic import BaseModel, ConfigDict
from models.users import Role


class EmployeeResponseDTO(BaseModel):
    id: str
    name: str
    email: str
    role: Role | str
    available: bool

    model_config = ConfigDict(extra="ignore")
