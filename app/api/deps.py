from app.core.config import get_settings
from app.infrastructure.database import OAuthStateStore, SQLiteDatabase, TokenStore, get_database
from app.infrastructure.google_calendar import GoogleCalendarClient
from app.services.calendar_service import CalendarService
from app.services.user_service import UserService


def get_database_instance() -> SQLiteDatabase:
    settings = get_settings()
    return get_database(settings)


def get_token_store() -> TokenStore:
    database = get_database_instance()
    return TokenStore(database)


def get_state_store() -> OAuthStateStore:
    database = get_database_instance()
    return OAuthStateStore(database)


def get_calendar_service() -> CalendarService:
    settings = get_settings()
    token_store = get_token_store()
    calendar_client = GoogleCalendarClient(token_store, settings)
    return CalendarService(calendar_client, settings.default_meeting_duration_minutes)


def get_user_service() -> UserService:
    return UserService()
