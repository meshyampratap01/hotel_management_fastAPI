from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    status_code: int
    message: str
    data: Optional[Any] = None


class ErrorResponse(APIResponse):
    status_code: int = 400
    message: str
