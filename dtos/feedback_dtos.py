from typing import Optional
from pydantic import BaseModel, Field


class CreateFeedbackDTO(BaseModel):
    message: str = Field(..., min_length=1)
    rating: Optional[int]
