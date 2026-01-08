from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Feedback(BaseModel):
    id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    user_name: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

    rating: Optional[int] = Field(None, ge=1, le=5)

    created_at: datetime
