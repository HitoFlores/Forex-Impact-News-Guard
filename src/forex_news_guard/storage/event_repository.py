from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path

from forex_news_guard.domain.models import ForexEvent, StoredEvent
from forex_news_guard.storage.json_state_store import JsonStateStore


class EventRepository:
    def __init__(self, state_path: str) -> None:
        self.store = JsonStateStore(self._resolve_state_path(state_path, ".events"))

    def replace_relevant_events(self, events: list[ForexEvent], reference_time: datetime) -> None:
        window_start, window_end = self._retention_window(reference_time)
        retained_events = [
            event
            for event in events
            if event.scheduled_at is not None and window_start <= event.scheduled_at <= window_end
        ]
        payload = {
            "relevant_events": [
                self._stored_event_payload(event=event, reference_time=reference_time) for event in retained_events
            ]
        }
        self.store.save(payload)

    def list_relevant_events(self, reference_time: datetime) -> list[StoredEvent]:
        self.cleanup(reference_time)
        payload = self.store.load(default={"relevant_events": []})
        rows = payload.get("relevant_events", [])
        events = [StoredEvent.model_validate(row) for row in rows]
        today = reference_time.date().isoformat()
        tomorrow = (reference_time.date() + timedelta(days=1)).isoformat()
        return sorted(
            [item for item in events if item.event_date in {today, tomorrow}],
            key=lambda item: (
                item.event.scheduled_at is None,
                item.event.scheduled_at or reference_time,
            ),
        )

    def cleanup(self, reference_time: datetime) -> None:
        payload = self.store.load(default={"relevant_events": []})
        rows = payload.get("relevant_events", [])
        today = reference_time.date().isoformat()
        tomorrow = (reference_time.date() + timedelta(days=1)).isoformat()
        payload["relevant_events"] = [
            row
            for row in rows
            if today <= row.get("event_date", "") <= tomorrow
        ]
        self.store.save(payload)

    def _retention_window(self, reference_time: datetime) -> tuple[datetime, datetime]:
        start = datetime.combine(reference_time.date(), time.min, tzinfo=reference_time.tzinfo)
        end = datetime.combine(reference_time.date() + timedelta(days=1), time.max, tzinfo=reference_time.tzinfo)
        return start, end

    def _stored_event_payload(self, event: ForexEvent, reference_time: datetime) -> dict[str, object]:
        scheduled_at = event.scheduled_at.astimezone(reference_time.tzinfo) if event.scheduled_at else None
        stored = StoredEvent(
            event=event,
            stored_at=reference_time,
            event_date=scheduled_at.date().isoformat() if scheduled_at else "",
        )
        return stored.model_dump(mode="json")

    def _resolve_state_path(self, state_path: str, suffix: str) -> str:
        path = Path(state_path)
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            return str(path.with_name(f"{path.stem}{suffix}.json"))
        return state_path
