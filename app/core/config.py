from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_base_url: str = "http://localhost:8000"
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    google_scopes: str = "https://www.googleapis.com/auth/calendar.events"
    sqlite_path: str = "app.db"
    vapi_public_key: str | None = None
    vapi_assistant_id: str | None = None
    default_meeting_duration_minutes: int = 30
    default_user_id: str = "default"

    @property
    def google_scopes_list(self) -> list[str]:
        return [scope.strip() for scope in self.google_scopes.split(",") if scope.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
