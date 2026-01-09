from pydantic import BaseModel, Field, field_validator
from datetime import date


class CreateBookingRequest(BaseModel):
    room_number: int = Field(..., gt=0)
    check_in_date: date
    check_out_date: date

    @field_validator("check_in_date")
    @classmethod
    def check_in_not_in_past(cls, check_in_date: date):
        if check_in_date < date.today():
            raise ValueError("check_in_date cannot be in the past")
        return check_in_date

    @field_validator("check_out_date")
    @classmethod
    def validate_dates(cls, check_out_date: date, info):
        check_in_date = info.data.get("check_in_date")

        if check_in_date is None:
            return check_out_date

        if check_out_date <= check_in_date:
            raise ValueError("check_out_date must be after check_in_date")

        return check_out_date
