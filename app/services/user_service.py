class UserService:
    def resolve_user_id(self, payload: dict) -> str | None:
        user_id = self._first_non_empty(
            self._read_path(payload, "customer", "id"),
            self._read_path(payload, "customer", "number"),
            self._read_path(payload, "metadata", "customer_id"),
            self._read_path(payload, "message", "metadata", "customer_id"),
            self._read_path(payload, "call", "metadata", "customer_id"),
            self._read_path(payload, "assistantOverrides", "metadata", "customer_id"),
            self._read_path(payload, "assistantOverrides", "variableValues", "customer_id"),
            self._read_path(payload, "message", "assistantOverrides", "metadata", "customer_id"),
            self._read_path(payload, "message", "assistantOverrides", "variableValues", "customer_id"),
        )
        return user_id

    def _read_path(self, payload: dict, *path: str) -> str | None:
        current: object = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        if current is None:
            return None
        return str(current)

    def _first_non_empty(self, *values: str | None) -> str | None:
        for value in values:
            if value is None:
                continue
            normalized = value.strip()
            if normalized:
                return normalized
        return None
