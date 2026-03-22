import base64
import hashlib
import hmac

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


async def verify_vapi_signature(request: Request) -> None:
    settings = get_settings()
    if not settings.vapi_signature_secret:
        return

    raw_signature = request.headers.get("X-Vapi-Signature")
    if not raw_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Vapi signature")

    body = await request.body()
    digest = hmac.new(
        settings.vapi_signature_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected_signatures = _build_expected_signatures(digest)
    candidates = _extract_signature_candidates(raw_signature)
    if not _is_valid_signature(candidates, expected_signatures):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Vapi signature")


def _build_expected_signatures(digest: bytes) -> set[str]:
    return {
        digest.hex(),
        base64.b64encode(digest).decode("utf-8"),
    }


def _extract_signature_candidates(raw_signature: str) -> list[str]:
    candidates: list[str] = []
    parts = [part.strip() for part in raw_signature.split(",") if part.strip()]
    if not parts:
        return []

    for part in parts:
        candidates.append(part)
        if "=" not in part:
            continue

        key, value = part.split("=", maxsplit=1)
        key = key.strip().lower()
        value = value.strip()
        if key in {"sha256", "v1", "signature"} and value:
            candidates.append(value)

    unique_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)
    return unique_candidates


def _is_valid_signature(candidates: list[str], expected_signatures: set[str]) -> bool:
    for candidate in candidates:
        for expected in expected_signatures:
            if hmac.compare_digest(candidate, expected):
                return True
    return False
