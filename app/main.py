import json

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from app.api.v1.endpoints import auth, vapi_webhook
from app.core.config import get_settings
from app.infrastructure.database import get_database


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Vapi Scheduler", version="1.0.0")

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(vapi_webhook.router, prefix="/api/v1")

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(customer_id: str = Query(..., min_length=1)) -> HTMLResponse:
        html = _build_dashboard_html(
            customer_id=customer_id,
            vapi_public_key=settings.vapi_public_key,
            vapi_assistant_id=settings.vapi_assistant_id,
        )
        return HTMLResponse(content=html)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.on_event("startup")
    def on_startup() -> None:
        database = get_database(settings)
        database.init_schema()

    return app


app = create_app()


def _build_dashboard_html(
    customer_id: str,
    vapi_public_key: str | None,
    vapi_assistant_id: str | None,
) -> str:
    has_vapi_config = bool(vapi_public_key and vapi_assistant_id)
    public_key_json = json.dumps(vapi_public_key or "")
    assistant_id_json = json.dumps(vapi_assistant_id or "")
    customer_id_json = json.dumps(customer_id)
    config_error_html = ""
    button_disabled = ""
    if not has_vapi_config:
        config_error_html = (
            "<p class='error'>Missing Vapi config. Add VAPI_PUBLIC_KEY and "
            "VAPI_ASSISTANT_ID in .env.</p>"
        )
        button_disabled = "disabled"

    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Voice Scheduler Dashboard</title>
    <style>
        :root {{
            --bg-start: #f4f7ff;
            --bg-end: #fdf6ec;
            --card: #ffffff;
            --ink: #1d2433;
            --muted: #5e6678;
            --brand: #0f6dff;
            --brand-strong: #0a47a3;
            --ok: #1d7f45;
            --error: #b42318;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            min-height: 100vh;
            font-family: "Segoe UI", "Helvetica Neue", sans-serif;
            color: var(--ink);
            background: radial-gradient(circle at 10% 20%, var(--bg-start), var(--bg-end));
            display: grid;
            place-items: center;
            padding: 24px;
        }}
        .card {{
            width: min(680px, 100%);
            background: var(--card);
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 12px 40px rgba(21, 33, 60, 0.12);
        }}
        h1 {{ margin: 0 0 8px; font-size: 1.7rem; }}
        p {{ margin: 0; color: var(--muted); line-height: 1.5; }}
        .meta {{ margin-top: 16px; font-size: 0.95rem; color: var(--muted); }}
        .controls {{ margin-top: 24px; display: flex; gap: 12px; flex-wrap: wrap; }}
        button {{
            border: 0;
            border-radius: 12px;
            padding: 14px 18px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            background: var(--brand);
            color: #fff;
            transition: transform 120ms ease, background 120ms ease;
        }}
        button:hover {{ background: var(--brand-strong); transform: translateY(-1px); }}
        button:disabled {{ background: #98a2b3; cursor: not-allowed; transform: none; }}
        #stop-button {{ background: #475467; }}
        #status {{ margin-top: 18px; font-weight: 600; color: var(--ink); }}
        #debug {{
            margin-top: 12px;
            padding: 10px;
            border-radius: 10px;
            background: #f2f4f7;
            color: #344054;
            font-size: 0.9rem;
            max-height: 180px;
            overflow: auto;
            white-space: pre-wrap;
        }}
        .ok {{ color: var(--ok); }}
        .error {{ color: var(--error); margin-top: 12px; font-weight: 600; }}
        @media (max-width: 640px) {{
            .card {{ padding: 22px; border-radius: 16px; }}
            h1 {{ font-size: 1.4rem; }}
            button {{ width: 100%; }}
        }}
    </style>
</head>
<body>
    <main class=\"card\">
        <h1>Calendar connected</h1>
        <p>Start a voice call and ask the assistant to schedule your meeting.</p>
        <p class=\"meta\">Connected user: <strong id=\"user-id\"></strong></p>
        {config_error_html}
        <div class=\"controls\">
            <button id=\"talk-button\" {button_disabled}>Start voice assistant</button>
            <button id=\"stop-button\" disabled>End call</button>
        </div>
        <p id=\"status\">Ready.</p>
        <pre id="debug">Diagnostics ready.</pre>
    </main>

    <script type="module">
        import Vapi from "https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/+esm";

        const vapiPublicKey = {public_key_json};
        const vapiAssistantId = {assistant_id_json};
        const customerId = {customer_id_json};

        const userIdEl = document.getElementById("user-id");
        const talkButton = document.getElementById("talk-button");
        const stopButton = document.getElementById("stop-button");
        const statusEl = document.getElementById("status");
        const debugEl = document.getElementById("debug");

        const logDebug = (message) => {{
            const timestamp = new Date().toISOString();
            debugEl.textContent += `\n[${{timestamp}}] ${{message}}`;
        }};

        userIdEl.innerText = customerId;

        if (vapiPublicKey && vapiAssistantId) {{
            logDebug("Vapi config found. Initializing SDK...");
            const vapi = new Vapi(vapiPublicKey);

            const setStatus = (text, cssClass = "") => {{
                statusEl.className = cssClass;
                statusEl.innerText = text;
            }};

            talkButton.addEventListener("click", async () => {{
                logDebug("Start button clicked.");
                talkButton.disabled = true;
                stopButton.disabled = false;
                setStatus("Starting voice call...");
                try {{
                    await vapi.start(vapiAssistantId, {{ variableValues: {{ customer_id: customerId }} }});
                    logDebug("vapi.start resolved successfully.");
                    setStatus("Listening...", "ok");
                }} catch (error) {{
                    talkButton.disabled = false;
                    stopButton.disabled = true;
                    logDebug(`vapi.start failed: ${{error?.message || error}}`);
                    setStatus(`Could not start call: ${{error.message || error}}`, "error");
                }}
            }});

            stopButton.addEventListener("click", () => {{
                logDebug("Stop button clicked.");
                vapi.stop();
            }});

            vapi.on("call-start", () => {{
                logDebug("Event: call-start");
                setStatus("Call connected.", "ok");
            }});

            vapi.on("call-end", () => {{
                logDebug("Event: call-end");
                talkButton.disabled = false;
                stopButton.disabled = true;
                setStatus("Call finished. Check your Google Calendar.", "ok");
            }});

            vapi.on("error", (error) => {{
                logDebug(`Event: error - ${{error?.message || error}}`);
                talkButton.disabled = false;
                stopButton.disabled = true;
                setStatus(`Call error: ${{error.message || error}}`, "error");
            }});
        }} else {{
            logDebug("Vapi config missing. Start button disabled.");
        }}
    </script>
</body>
</html>
"""
