import importlib

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.v1.endpoints import auth


class FakeSettings:
    google_client_id = "client-id"
    google_client_secret = "client-secret"
    google_redirect_uri = "http://localhost:8000/api/v1/auth/google/callback"
    google_scopes_list = ["https://www.googleapis.com/auth/calendar.events"]
    default_user_id = "default"


class FakeStateStore:
    def __init__(self, user_id: str | None = None) -> None:
        self._user_id = user_id
        self.received_customer_id = None

    def create_state(self, user_id: str) -> str:
        self.received_customer_id = user_id
        return "state-123"

    def consume_state(self, state: str) -> str | None:
        if state != "state-123":
            return None
        return self._user_id


class FakeTokenStore:
    def __init__(self) -> None:
        self.saved_user_id = None
        self.saved_token = None
        self.saved_records = []

    def save_tokens(self, user_id: str, token_json: str) -> None:
        self.saved_user_id = user_id
        self.saved_token = token_json
        self.saved_records.append((user_id, token_json))


class FakeCredentials:
    def to_json(self) -> str:
        return '{"access_token":"token"}'


class FakeFlow:
    def __init__(self) -> None:
        self.redirect_uri = None
        self.credentials = FakeCredentials()

    @classmethod
    def from_client_config(cls, client_config, scopes, state):
        return cls()

    def authorization_url(self, access_type, include_granted_scopes, prompt):
        return "https://accounts.google.com/o/oauth2/auth?x=1", "ignored"

    def fetch_token(self, code: str) -> None:
        if not code:
            raise ValueError("missing code")


def test_start_google_auth_uses_customer_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "Flow", FakeFlow)
    state_store = FakeStateStore()

    response = auth.start_google_auth(
        customer_id="customer-42",
        settings=FakeSettings(),
        state_store=state_store,
    )

    assert state_store.received_customer_id == "customer-42"
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/auth")


def test_start_google_auth_generates_customer_id_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "Flow", FakeFlow)
    state_store = FakeStateStore()

    response = auth.start_google_auth(
        customer_id=None,
        settings=FakeSettings(),
        state_store=state_store,
    )

    assert state_store.received_customer_id is not None
    assert state_store.received_customer_id.startswith("user-")
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/auth")


def test_google_auth_callback_saves_tokens_for_state_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth, "Flow", FakeFlow)
    state_store = FakeStateStore(user_id="customer-42")
    token_store = FakeTokenStore()

    response = auth.google_auth_callback(
        code="oauth-code",
        state="state-123",
        settings=FakeSettings(),
        state_store=state_store,
        token_store=token_store,
    )

    assert ("customer-42", '{"access_token":"token"}') in token_store.saved_records
    assert ("default", '{"access_token":"token"}') in token_store.saved_records
    assert response.headers["location"] == "/dashboard?customer_id=customer-42"


def test_google_auth_callback_rejects_invalid_state() -> None:
    state_store = FakeStateStore(user_id=None)
    token_store = FakeTokenStore()

    with pytest.raises(HTTPException) as error:
        auth.google_auth_callback(
            code="oauth-code",
            state="state-123",
            settings=FakeSettings(),
            state_store=state_store,
            token_store=token_store,
        )

    assert error.value.status_code == 400


def test_dashboard_route_renders_customer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "public-key")
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "assistant-id")

    import app.core.config as config_module

    config_module.get_settings.cache_clear()

    import app.main as main_module

    main_module = importlib.reload(main_module)
    client = TestClient(main_module.create_app())

    response = client.get("/dashboard", params={"customer_id": "customer-42"})

    assert response.status_code == 200
    assert "customer-42" in response.text
    assert "Missing Vapi config" not in response.text
