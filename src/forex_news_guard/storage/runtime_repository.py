from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from forex_news_guard.domain.runtime import AlertDispatchRecord, AlertExecutionKind, DeliveryChannel


class RuntimeRepository:
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
                CREATE TABLE IF NOT EXISTS dispatched_alerts (
                    event_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    scheduled_for TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    PRIMARY KEY (event_id, kind, attempt, scheduled_for)
                )
                """
            )
            connection.commit()

    def has_been_dispatched(
        self,
        event_id: str,
        kind: AlertExecutionKind,
        scheduled_for: datetime,
        attempt: int = 1,
    ) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM dispatched_alerts
                WHERE event_id = ? AND kind = ? AND attempt = ? AND scheduled_for = ?
                """,
                (event_id, kind.value, attempt, scheduled_for.isoformat()),
            ).fetchone()
        return row is not None

    def record_dispatch(self, record: AlertDispatchRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO dispatched_alerts (
                    event_id, kind, attempt, scheduled_for, sent_at, channel
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.event_id,
                    record.kind.value,
                    record.attempt,
                    record.scheduled_for.isoformat(),
                    record.sent_at.isoformat(),
                    record.channel.value,
                ),
            )
            connection.commit()
