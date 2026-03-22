from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.schemas import MeetingRequest
from app.services.calendar_service import CalendarService


class FakeCalendarClient:
    def __init__(self) -> None:
        self.last_payload = None

    def create_event(self, user_id, summary, description, start, end, timezone):
        self.last_payload = {
            "user_id": user_id,
            "summary": summary,
            "description": description,
            "start": start,
            "end": end,
            "timezone": timezone,
        }
        return type("Result", (), {"event_id": "evt", "html_link": "link"})


def test_calendar_service_builds_timezone_aware_times() -> None:
    client = FakeCalendarClient()
    service = CalendarService(client, 30)
    meeting = MeetingRequest(
        name="Sam",
        date="2026-03-20",
        time="09:00",
        timezone="America/Chicago",
        title="Sync",
    )

    service.create_event("user", meeting)
    payload = client.last_payload

    assert payload["start"] == datetime(2026, 3, 20, 9, 0, tzinfo=ZoneInfo("America/Chicago"))
    assert payload["end"] == datetime(2026, 3, 20, 9, 30, tzinfo=ZoneInfo("America/Chicago"))
