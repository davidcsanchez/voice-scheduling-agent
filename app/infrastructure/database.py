import base64
import os
import sqlite3
from datetime import datetime

from app.core.config import Settings


class SQLiteDatabase:
    def __init__(self, path: str) -> None:
        self._path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_schema(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    user_id TEXT PRIMARY KEY,
                    token_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_state (
                    state TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()


class TokenStore:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def save_tokens(self, user_id: str, token_json: str) -> None:
        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO tokens (user_id, token_json)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET token_json = excluded.token_json
                """,
                (user_id, token_json),
            )
            connection.commit()

    def load_tokens(self, user_id: str) -> str | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT token_json FROM tokens WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return row["token_json"] if row else None


class OAuthStateStore:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def create_state(self) -> str:
        state = self._generate_state()
        with self._database.connect() as connection:
            connection.execute(
                "INSERT INTO oauth_state (state, created_at) VALUES (?, ?)",
                (state, datetime.utcnow().isoformat()),
            )
            connection.commit()
        return state

    def consume_state(self, state: str) -> bool:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT state FROM oauth_state WHERE state = ?",
                (state,),
            ).fetchone()
            if not row:
                return False
            connection.execute("DELETE FROM oauth_state WHERE state = ?", (state,))
            connection.commit()
        return True

    def _generate_state(self) -> str:
        return base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8")


def get_database(settings: Settings) -> SQLiteDatabase:
    return SQLiteDatabase(settings.sqlite_path)
