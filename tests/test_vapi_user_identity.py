from app.api.v1.endpoints.vapi_webhook import _require_user_id


def test_require_user_id_accepts_non_empty_value() -> None:
    assert _require_user_id("user-123") == "user-123"


def test_require_user_id_rejects_missing_value() -> None:
    try:
        _require_user_id(None)
    except ValueError as error:
        assert "Missing customer identity" in str(error)
        return

    raise AssertionError("Expected ValueError for missing user id")
