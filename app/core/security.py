import hashlib
import hmac

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


async def verify_vapi_signature(request: Request) -> None:
    settings = get_settings()
    if not settings.vapi_signature_secret:
        return

    signature = request.headers.get("X-Vapi-Signature")
    if not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Vapi signature")

    body = await request.body()
    expected = hmac.new(
        settings.vapi_signature_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Vapi signature")
