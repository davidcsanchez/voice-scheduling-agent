from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


class MeetingRequest(BaseModel):
    name: str = Field(min_length=1)
    date: str
    time: str
    timezone: str
    title: str = Field(min_length=1)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        datetime.strptime(value, "%Y-%m-%d")
        return value

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        datetime.strptime(value, "%H:%M")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Invalid timezone") from exc
        return value
