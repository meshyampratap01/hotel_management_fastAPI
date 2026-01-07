from pydantic import BaseModel, Field
from models.service_request import ServiceType


class CreateServiceRequest(BaseModel):
    room_num: int = Field(
        ...,
        gt=0,
        description="Room number must be positive",
        example=101,
    )

    type: ServiceType = Field(
        ...,
        description="Type of service requested",
        example="Cleaning",
    )

    details: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Additional details for the service request",
        example="AC is not working",
    )


class assign_service_request_dto(BaseModel):
    employee_id: str
