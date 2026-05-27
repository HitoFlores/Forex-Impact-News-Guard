from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from forex_news_guard.domain.models import AlertPolicy


class SettingsRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    settings_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get_policy(self) -> AlertPolicy:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM app_settings WHERE settings_key = ?",
                ("alert_policy",),
            ).fetchone()
        if row is None:
            policy = AlertPolicy()
            self.save_policy(policy)
            return policy
        return AlertPolicy.model_validate(json.loads(row["payload"]))

    def save_policy(self, policy: AlertPolicy) -> AlertPolicy:
        payload = json.dumps(policy.model_dump(mode="json"))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_settings (settings_key, payload)
                VALUES (?, ?)
                ON CONFLICT(settings_key) DO UPDATE SET payload = excluded.payload
                """,
                ("alert_policy", payload),
            )
            connection.commit()
        return policy
