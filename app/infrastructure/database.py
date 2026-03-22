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
                    created_at TEXT NOT NULL,
                    user_id TEXT NOT NULL
                )
                """
            )
            self._ensure_oauth_state_user_id_column(connection)
            connection.commit()

    def _ensure_oauth_state_user_id_column(self, connection: sqlite3.Connection) -> None:
        columns = connection.execute("PRAGMA table_info(oauth_state)").fetchall()
        has_user_id_column = any(column[1] == "user_id" for column in columns)
        if has_user_id_column:
            return
        connection.execute(
            "ALTER TABLE oauth_state ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'"
        )


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

    def create_state(self, user_id: str) -> str:
        state = self._generate_state()
        with self._database.connect() as connection:
            connection.execute(
                "INSERT INTO oauth_state (state, created_at, user_id) VALUES (?, ?, ?)",
                (state, datetime.utcnow().isoformat(), user_id),
            )
            connection.commit()
        return state

    def consume_state(self, state: str) -> str | None:
        with self._database.connect() as connection:
            row = connection.execute(
                "SELECT user_id FROM oauth_state WHERE state = ?",
                (state,),
            ).fetchone()
            if not row:
                return None
            connection.execute("DELETE FROM oauth_state WHERE state = ?", (state,))
            connection.commit()
        return str(row["user_id"])

    def _generate_state(self) -> str:
        return base64.urlsafe_b64encode(os.urandom(24)).decode("utf-8")


def get_database(settings: Settings) -> SQLiteDatabase:
    return SQLiteDatabase(settings.sqlite_path)
