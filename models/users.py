from models import roles
from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    email: str
    password: str
    role: roles.Role
    available: bool
