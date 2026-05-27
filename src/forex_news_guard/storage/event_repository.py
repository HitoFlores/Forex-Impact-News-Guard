from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Iterator

from forex_news_guard.domain.models import ForexEvent, StoredEvent


class EventRepository:
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
                CREATE TABLE IF NOT EXISTS relevant_events (
                    event_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    scheduled_at TEXT,
                    published_at TEXT,
                    actual TEXT,
                    forecast TEXT,
                    previous TEXT,
                    actual_better_worse INTEGER,
                    url TEXT,
                    source TEXT NOT NULL,
                    is_breaking INTEGER NOT NULL,
                    stored_at TEXT NOT NULL,
                    event_date TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_relevant_events_event_date ON relevant_events(event_date)"
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(relevant_events)").fetchall()
            }
            if "actual_better_worse" not in columns:
                connection.execute("ALTER TABLE relevant_events ADD COLUMN actual_better_worse INTEGER")
            connection.commit()

    def replace_relevant_events(self, events: list[ForexEvent], reference_time: datetime) -> None:
        window_start, window_end = self._retention_window(reference_time)
        retained_events = [
            event
            for event in events
            if event.scheduled_at is not None and window_start <= event.scheduled_at <= window_end
        ]
        with self._connect() as connection:
            self._cleanup_outside_window(connection, reference_time)
            self._delete_events_in_window(connection, reference_time)
            for event in retained_events:
                scheduled_at = event.scheduled_at.astimezone(reference_time.tzinfo) if event.scheduled_at else None
                connection.execute(
                    """
                    INSERT INTO relevant_events (
                        event_id, title, currency, impact, scheduled_at, published_at,
                        actual, forecast, previous, actual_better_worse, url, source, is_breaking, stored_at, event_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        title = excluded.title,
                        currency = excluded.currency,
                        impact = excluded.impact,
                        scheduled_at = excluded.scheduled_at,
                        published_at = excluded.published_at,
                        actual = excluded.actual,
                        forecast = excluded.forecast,
                        previous = excluded.previous,
                        actual_better_worse = excluded.actual_better_worse,
                        url = excluded.url,
                        source = excluded.source,
                        is_breaking = excluded.is_breaking,
                        stored_at = excluded.stored_at,
                        event_date = excluded.event_date
                    """,
                    (
                        event.id,
                        event.title,
                        event.currency,
                        event.impact.value,
                        event.scheduled_at.isoformat() if event.scheduled_at else None,
                        event.published_at.isoformat() if event.published_at else None,
                        event.actual,
                        event.forecast,
                        event.previous,
                        event.actual_better_worse,
                        event.url,
                        event.source,
                        int(event.is_breaking),
                        reference_time.isoformat(),
                        scheduled_at.date().isoformat() if scheduled_at else "",
                    ),
                )
            connection.commit()

    def list_relevant_events(self, reference_time: datetime) -> list[StoredEvent]:
        self.cleanup(reference_time)
        today = reference_time.date().isoformat()
        tomorrow = (reference_time.date() + timedelta(days=1)).isoformat()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM relevant_events
                WHERE event_date IN (?, ?)
                ORDER BY scheduled_at ASC
                """,
                (today, tomorrow),
            ).fetchall()
        return [self._row_to_stored_event(row) for row in rows]

    def cleanup(self, reference_time: datetime) -> None:
        with self._connect() as connection:
            self._cleanup_outside_window(connection, reference_time)
            connection.commit()

    def _delete_events_in_window(self, connection: sqlite3.Connection, reference_time: datetime) -> None:
        today = reference_time.date().isoformat()
        tomorrow = (reference_time.date() + timedelta(days=1)).isoformat()
        connection.execute(
            "DELETE FROM relevant_events WHERE event_date IN (?, ?)",
            (today, tomorrow),
        )

    def _cleanup_outside_window(self, connection: sqlite3.Connection, reference_time: datetime) -> None:
        today = reference_time.date().isoformat()
        tomorrow = (reference_time.date() + timedelta(days=1)).isoformat()
        connection.execute(
            "DELETE FROM relevant_events WHERE event_date < ? OR event_date > ?",
            (today, tomorrow),
        )

    def _retention_window(self, reference_time: datetime) -> tuple[datetime, datetime]:
        start = datetime.combine(reference_time.date(), time.min, tzinfo=reference_time.tzinfo)
        end = datetime.combine(reference_time.date() + timedelta(days=1), time.max, tzinfo=reference_time.tzinfo)
        return start, end

    def _row_to_stored_event(self, row: sqlite3.Row) -> StoredEvent:
        return StoredEvent(
            event=ForexEvent(
                id=row["event_id"],
                title=row["title"],
                currency=row["currency"],
                impact=row["impact"],
                scheduled_at=datetime.fromisoformat(row["scheduled_at"]) if row["scheduled_at"] else None,
                published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
                actual=row["actual"],
                forecast=row["forecast"],
                previous=row["previous"],
                actual_better_worse=row["actual_better_worse"],
                url=row["url"],
                source=row["source"],
                is_breaking=bool(row["is_breaking"]),
            ),
            stored_at=datetime.fromisoformat(row["stored_at"]),
            event_date=row["event_date"],
        )
