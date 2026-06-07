from __future__ import annotations

from datetime import datetime
from pathlib import Path

from forex_news_guard.domain.runtime import AlertDispatchRecord, AlertExecutionKind
from forex_news_guard.storage.json_state_store import JsonStateStore


class RuntimeRepository:
    def __init__(self, state_path: str) -> None:
        self.store = JsonStateStore(self._resolve_state_path(state_path, ".runtime"))

    def has_been_dispatched(
        self,
        event_id: str,
        kind: AlertExecutionKind,
        scheduled_for: datetime,
        attempt: int = 1,
    ) -> bool:
        for record in self._load_records():
            if (
                record["event_id"] == event_id
                and record["kind"] == kind.value
                and record["attempt"] == attempt
                and record["scheduled_for"] == scheduled_for.isoformat()
            ):
                return True
        return False

    def record_dispatch(self, record: AlertDispatchRecord) -> None:
        payload = self.store.load(default={"dispatched_alerts": []})
        rows = payload.get("dispatched_alerts", [])
        rows = [
            row
            for row in rows
            if not (
                row.get("event_id") == record.event_id
                and row.get("kind") == record.kind.value
                and row.get("attempt") == record.attempt
                and row.get("scheduled_for") == record.scheduled_for.isoformat()
            )
        ]
        rows.append(record.model_dump(mode="json"))
        payload["dispatched_alerts"] = rows
        self.store.save(payload)

    def _load_records(self) -> list[dict[str, object]]:
        payload = self.store.load(default={"dispatched_alerts": []})
        return payload.get("dispatched_alerts", [])

    def _resolve_state_path(self, state_path: str, suffix: str) -> str:
        path = Path(state_path)
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            return str(path.with_name(f"{path.stem}{suffix}.json"))
        return state_path
