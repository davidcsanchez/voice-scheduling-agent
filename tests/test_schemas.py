import pytest
from pydantic import ValidationError

from app.domain.schemas import MeetingRequest


def test_meeting_request_valid() -> None:
    meeting = MeetingRequest(
        name="Alex",
        date="2026-03-20",
        time="10:30",
        timezone="America/New_York",
        title="Demo",
    )
    assert meeting.name == "Alex"


def test_meeting_request_invalid_timezone() -> None:
    with pytest.raises(ValidationError):
        MeetingRequest(
            name="Alex",
            date="2026-03-20",
            time="10:30",
            timezone="Mars/Phobos",
            title="Demo",
        )
