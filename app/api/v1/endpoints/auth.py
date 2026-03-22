from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow

from app.api.deps import get_state_store, get_token_store
from app.core.config import Settings, get_settings

router = APIRouter(tags=["auth"])


@router.get("/auth/google/start")
def start_google_auth(
    settings: Settings = Depends(get_settings),
    state_store=Depends(get_state_store),
) -> RedirectResponse:
    state = state_store.create_state()
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


@router.get("/auth/google/callback")
def google_auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    settings: Settings = Depends(get_settings),
    state_store=Depends(get_state_store),
    token_store=Depends(get_token_store),
) -> HTMLResponse:
    if not state_store.consume_state(state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

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
    token_store.save_tokens(settings.default_user_id, credentials_json)

    html = """
    <html>
      <body>
        <h3>Google Calendar connected.</h3>
        <p>You can close this window.</p>
        <script>window.close();</script>
      </body>
    </html>
    """
    return HTMLResponse(html)
