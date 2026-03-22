import base64
import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def verify_vapi_signature(request: Request) -> None:
    settings = get_settings()
    signature_secret = _normalize_signature_secret(settings.vapi_signature_secret)
    if signature_secret is None:
        logger.info("Vapi signature validation disabled for webhook request.")
        return

    raw_signature = request.headers.get("X-Vapi-Signature")
    if not raw_signature:
        logger.warning("Vapi webhook rejected: missing X-Vapi-Signature header.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Vapi signature")

    body = await request.body()
    digest = hmac.new(
        signature_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected_signatures = _build_expected_signatures(digest)
    candidates = _extract_signature_candidates(raw_signature)
    if not _is_valid_signature(candidates, expected_signatures):
        logger.warning(
            "Vapi webhook rejected: invalid signature format/value. candidates=%s",
            len(candidates),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Vapi signature")


def _normalize_signature_secret(raw_secret: str | None) -> str | None:
    if raw_secret is None:
        return None

    normalized = raw_secret.strip()
    if not normalized:
        return None

    lowered = normalized.lower()
    if lowered in {"none", "null", "disabled", "false"}:
        return None
    return normalized


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
