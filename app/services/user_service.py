class UserService:
    def __init__(self, default_user_id: str) -> None:
        self._default_user_id = default_user_id

    def resolve_user_id(self, payload: dict) -> str:
        customer = payload.get("customer") or {}
        user_id = customer.get("id") or customer.get("number")
        if user_id:
            return str(user_id)
        return self._default_user_id
