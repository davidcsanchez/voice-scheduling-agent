from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalendarEventResult:
    event_id: str
    html_link: str


@dataclass(frozen=True)
class MeetingDetails:
    name: str
    title: str
    start: datetime
    end: datetime
    timezone: str
