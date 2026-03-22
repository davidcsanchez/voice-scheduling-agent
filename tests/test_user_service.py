from app.services.user_service import UserService


def test_resolve_user_id_prefers_customer_id() -> None:
    service = UserService()
    payload = {"customer": {"id": "cust-1", "number": "+15550001"}}

    resolved = service.resolve_user_id(payload)

    assert resolved == "cust-1"


def test_resolve_user_id_uses_metadata_customer_id() -> None:
    service = UserService()
    payload = {"metadata": {"customer_id": "meta-42"}}

    resolved = service.resolve_user_id(payload)

    assert resolved == "meta-42"


def test_resolve_user_id_uses_assistant_overrides_variable_values() -> None:
    service = UserService()
    payload = {
        "assistantOverrides": {
            "variableValues": {
                "customer_id": "override-7",
            }
        }
    }

    resolved = service.resolve_user_id(payload)

    assert resolved == "override-7"


def test_resolve_user_id_returns_none_when_missing() -> None:
    service = UserService()

    resolved = service.resolve_user_id({})

    assert resolved is None
