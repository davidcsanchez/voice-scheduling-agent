from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.models import CalendarEventResult, MeetingDetails
from app.domain.schemas import MeetingRequest


class CalendarService:
    def __init__(self, calendar_client, duration_minutes: int) -> None:
        self._calendar_client = calendar_client
        self._duration_minutes = duration_minutes

    def create_event(self, user_id: str, meeting: MeetingRequest) -> dict:
        details = self._build_details(meeting)
        result = self._calendar_client.create_event(
            user_id=user_id,
            summary=details.title,
            description=f"Meeting with {details.name}",
            start=details.start,
            end=details.end,
            timezone=details.timezone,
        )
        return {"eventId": result.event_id, "htmlLink": result.html_link}

    def _build_details(self, meeting: MeetingRequest) -> MeetingDetails:
        start = self._parse_start(meeting)
        end = start + timedelta(minutes=self._duration_minutes)
        return MeetingDetails(
            name=meeting.name,
            title=meeting.title,
            start=start,
            end=end,
            timezone=meeting.timezone,
        )

    def _parse_start(self, meeting: MeetingRequest) -> datetime:
        timezone = ZoneInfo(meeting.timezone)
        start_date = datetime.strptime(meeting.date, "%Y-%m-%d").date()
        start_time = datetime.strptime(meeting.time, "%H:%M").time()
        return datetime.combine(start_date, start_time, tzinfo=timezone)
