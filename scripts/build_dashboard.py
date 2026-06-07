from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from forex_news_guard.domain.models import AlertPolicy, StoredEvent
from forex_news_guard.domain.runtime import AlertDispatchRecord
from forex_news_guard.services.event_scheduler import build_event_schedules


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".state"
PUBLIC_DIR = ROOT / "public"


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def build_dashboard_payload(
    policy_payload: object,
    events_payload: object,
    runtime_payload: object,
    keepalive_payload: object,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    policy = AlertPolicy.model_validate(policy_payload or {})
    stored_events = [
        StoredEvent.model_validate(row)
        for row in (events_payload or {}).get("relevant_events", [])
    ]
    dispatches = [
        AlertDispatchRecord.model_validate(row)
        for row in (runtime_payload or {}).get("dispatched_alerts", [])
    ]
    schedules = build_event_schedules([item.event for item in stored_events], policy)
    now = generated_at or datetime.now(tz=policy.timezone_info)
    next_event_at = min(
        (item.event.scheduled_at for item in stored_events if item.event.scheduled_at is not None),
        default=None,
    )
    latest_stored_at = max((item.stored_at for item in stored_events), default=None)
    last_dispatch_at = max((item.sent_at for item in dispatches), default=None)
    next_alert_at = min((schedule.alert.scheduled_for for schedule in schedules), default=None)
    dispatch_breakdown = Counter(item.kind.value for item in dispatches)
    monitored_currencies = sorted(policy.normalized_currencies)

    return {
        "generated_at": now.isoformat(),
        "policy": policy.model_dump(mode="json"),
        "policy_summary": {
            "timezone": policy.timezone,
            "lead_minutes": policy.lead_minutes,
            "revalidate_minutes_before_alert": policy.revalidate_minutes_before_alert,
            "result_check_delay_minutes": policy.result_check_delay_minutes,
            "result_retry_minutes": policy.result_retry_minutes,
            "daily_summary_enabled": policy.daily_summary_enabled,
            "include_results": policy.include_results,
            "high_impact_only": policy.high_impact_only,
            "breaking_enabled": policy.breaking_enabled,
            "calendar_enabled": policy.calendar_enabled,
            "monitored_currencies": monitored_currencies,
        },
        "counts": {
            "relevant_events": len(stored_events),
            "schedules": len(schedules),
            "dispatches": len(dispatches),
            "tracked_currencies": len(monitored_currencies),
        },
        "status": {
            "generated_at": now.isoformat(),
            "next_event_at": next_event_at.isoformat() if next_event_at else None,
            "next_alert_at": next_alert_at.isoformat() if next_alert_at else None,
            "latest_event_stored_at": latest_stored_at.isoformat() if latest_stored_at else None,
            "last_dispatch_at": last_dispatch_at.isoformat() if last_dispatch_at else None,
            "keepalive_updated_at": (keepalive_payload or {}).get("updated_at"),
        },
        "dispatch_breakdown": [
            {"kind": kind, "count": count}
            for kind, count in sorted(dispatch_breakdown.items())
        ],
        "next_alerts": [
            {
                "event_id": schedule.event.id,
                "title": schedule.event.title,
                "currency": schedule.event.currency,
                "impact": schedule.event.impact.value,
                "alert_kind": schedule.alert.kind.value,
                "alert_at": schedule.alert.scheduled_for.isoformat(),
                "scheduled_at": schedule.event.scheduled_at.isoformat() if schedule.event.scheduled_at else None,
                "risk_window_starts_at": (
                    (schedule.event.scheduled_at - policy.risk_before_delta).isoformat()
                    if schedule.event.scheduled_at
                    else None
                ),
                "risk_window_ends_at": (
                    (schedule.event.scheduled_at + policy.risk_after_delta).isoformat()
                    if schedule.event.scheduled_at
                    else None
                ),
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
                "actual": item.event.actual,
                "forecast": item.event.forecast,
                "previous": item.event.previous,
                "is_breaking": item.event.is_breaking,
            }
            for item in stored_events[:12]
        ],
        "recent_dispatches": [
            record.model_dump(mode="json")
            for record in sorted(dispatches, key=lambda item: item.sent_at, reverse=True)[:12]
        ],
    }


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    policy_payload = load_json(STATE_DIR / "settings.json", {})
    events_payload = load_json(STATE_DIR / "events.json", {"relevant_events": []})
    runtime_payload = load_json(STATE_DIR / "runtime.json", {"dispatched_alerts": []})
    keepalive_payload = load_json(STATE_DIR / "keepalive.json", {})

    dashboard = build_dashboard_payload(
        policy_payload,
        events_payload,
        runtime_payload,
        keepalive_payload,
    )

    (PUBLIC_DIR / "state.json").write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
