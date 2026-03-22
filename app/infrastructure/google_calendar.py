import json
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import Settings
from app.domain.models import CalendarEventResult

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    def __init__(self, token_store, settings: Settings) -> None:
        self._token_store = token_store
        self._settings = settings

    def create_event(
        self,
        user_id: str,
        summary: str,
        description: str,
        start,
        end,
        timezone: str,
    ) -> CalendarEventResult:
        logger.info("Creating Google Calendar event. user_id=%s", user_id)
        credentials = self._load_credentials(user_id)
        service = build("calendar", "v3", credentials=credentials)
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end.isoformat(), "timeZone": timezone},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        logger.info(
            "Google Calendar event created. user_id=%s event_id=%s",
            user_id,
            created.get("id", ""),
        )
        return CalendarEventResult(
            event_id=created.get("id", ""),
            html_link=created.get("htmlLink", ""),
        )

    def _load_credentials(self, user_id: str) -> Credentials:
        token_json = self._token_store.load_tokens(user_id)
        if not token_json:
            raise ValueError("Google OAuth not completed for this user")

        info = json.loads(token_json)
        logger.info("Building credentials from stored tokens. user_id=%s", user_id)
        credentials = Credentials.from_authorized_user_info(
            info,
            scopes=self._settings.google_scopes_list,
        )
        if credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired Google OAuth token. user_id=%s", user_id)
            credentials.refresh(Request())
            self._token_store.save_tokens(user_id, credentials.to_json())
        return credentials
