from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from forex_news_guard.domain.models import AlertPolicy, StoredEvent
from forex_news_guard.services.event_scheduler import build_event_schedules


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".state"
PUBLIC_DIR = ROOT / "public"


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    policy_payload = load_json(STATE_DIR / "settings.json", {})
    events_payload = load_json(STATE_DIR / "events.json", {"relevant_events": []})
    runtime_payload = load_json(STATE_DIR / "runtime.json", {"dispatched_alerts": []})

    policy = AlertPolicy.model_validate(policy_payload or {})
    stored_events = [
        StoredEvent.model_validate(row)
        for row in events_payload.get("relevant_events", [])
    ]
    schedules = build_event_schedules([item.event for item in stored_events], policy)
    now = datetime.now(tz=policy.timezone_info)

    dashboard = {
        "generated_at": now.isoformat(),
        "policy": policy.model_dump(mode="json"),
        "counts": {
            "relevant_events": len(stored_events),
            "schedules": len(schedules),
            "dispatches": len(runtime_payload.get("dispatched_alerts", [])),
        },
        "next_alerts": [
            {
                "event_id": schedule.event.id,
                "title": schedule.event.title,
                "currency": schedule.event.currency,
                "impact": schedule.event.impact.value,
                "alert_at": schedule.alert.scheduled_for.isoformat(),
                "scheduled_at": schedule.event.scheduled_at.isoformat() if schedule.event.scheduled_at else None,
            }
            for schedule in schedules[:10]
        ],
        "recent_events": [
            {
                "event_id": item.event.id,
                "title": item.event.title,
                "currency": item.event.currency,
                "impact": item.event.impact.value,
                "scheduled_at": item.event.scheduled_at.isoformat() if item.event.scheduled_at else None,
                "stored_at": item.stored_at.isoformat(),
            }
            for item in stored_events[:12]
        ],
        "recent_dispatches": list(reversed(runtime_payload.get("dispatched_alerts", [])))[:12],
    }

    (PUBLIC_DIR / "state.json").write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
