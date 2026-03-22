from urllib.parse import urlencode
from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from app.api.deps import get_state_store, get_token_store
from app.core.config import Settings, get_settings

router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/auth/google/start")
def start_google_auth(
    customer_id: str | None = Query(default=None),
    settings: Settings = Depends(get_settings),
    state_store=Depends(get_state_store),
) -> RedirectResponse:
    resolved_customer_id = _resolve_customer_id(customer_id)
    logger.info("Starting Google OAuth flow. resolved_customer_id=%s", resolved_customer_id)
    state = state_store.create_state(resolved_customer_id)
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.google_scopes_list,
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


def _resolve_customer_id(customer_id: str | None) -> str:
    if customer_id and customer_id.strip():
        return customer_id.strip()
    return f"user-{uuid4().hex}"


@router.get("/auth/google/callback")
def google_auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    settings: Settings = Depends(get_settings),
    state_store=Depends(get_state_store),
    token_store=Depends(get_token_store),
) -> RedirectResponse:
    user_id = state_store.consume_state(state)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    logger.info("Google OAuth callback accepted. resolved_user_id=%s", user_id)

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=settings.google_scopes_list,
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)

    credentials_json = flow.credentials.to_json()
    token_store.save_tokens(user_id, credentials_json)
    logger.warning("Google OAuth tokens persisted. resolved_user_id=%s", user_id)

    query = urlencode({"customer_id": user_id})
    return RedirectResponse(
        url=f"/dashboard?{query}",
        status_code=status.HTTP_302_FOUND,
    )
