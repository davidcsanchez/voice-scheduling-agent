from fastapi import FastAPI

from app.api.v1.endpoints import auth, vapi_webhook
from app.core.config import get_settings
from app.infrastructure.database import get_database


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Vapi Scheduler", version="1.0.0")

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(vapi_webhook.router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.on_event("startup")
    def on_startup() -> None:
        database = get_database(settings)
        database.init_schema()

    return app


app = create_app()
