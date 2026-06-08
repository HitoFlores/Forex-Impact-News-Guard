from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from forex_news_guard.domain.models import AlertPolicy, StoredEvent
from forex_news_guard.domain.runtime import (
    AlertDispatchRecord,
    RuntimeObservability,
    RuntimeProbeState,
    RuntimeProbeStatus,
)
from forex_news_guard.services.event_scheduler import build_event_schedules


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".state"
PUBLIC_DIR = ROOT / "public"


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def impact_rank(value: str) -> int:
    return {
        "high": 3,
        "medium": 2,
        "low": 1,
    }.get(value, 0)


def trigger_label(event_name: str | None) -> str:
    return {
        "schedule": "Cron GitHub",
        "workflow_dispatch": "Manual",
        "push": "Push",
        "pull_request": "Pull request",
    }.get(event_name or "", "Local")


def build_workflow_meta() -> dict[str, object]:
    event_name = os.getenv("GITHUB_EVENT_NAME")
    run_id = os.getenv("GITHUB_RUN_ID")
    repository = os.getenv("GITHUB_REPOSITORY")
    server_url = os.getenv("GITHUB_SERVER_URL")
    run_url = None
    if run_id and repository and server_url:
        run_url = f"{server_url}/{repository}/actions/runs/{run_id}"
    return {
        "name": os.getenv("GITHUB_WORKFLOW"),
        "event_name": event_name,
        "event_label": trigger_label(event_name),
        "actor": os.getenv("GITHUB_ACTOR"),
        "ref_name": os.getenv("GITHUB_REF_NAME"),
        "run_id": run_id,
        "run_number": os.getenv("GITHUB_RUN_NUMBER"),
        "repository": repository,
        "run_url": run_url,
    }


def summarize_component(
    name: str,
    record: RuntimeProbeState,
    generated_at: datetime,
) -> dict[str, object]:
    last_signal_at = record.last_attempt_at or record.last_success_at or record.last_error_at
    tone = record.status.value
    note = "Operativo"
    hint = "Sin accion inmediata."
    if not last_signal_at:
        tone = RuntimeProbeStatus.WARN.value
        note = "Sin muestras"
        hint = "Esperando primer ciclo util."
    elif record.status == RuntimeProbeStatus.OK and name == "scraping":
        age_minutes = max(0, int((generated_at - last_signal_at).total_seconds() // 60))
        if age_minutes > 30:
            tone = RuntimeProbeStatus.WARN.value
            note = f"Stale {age_minutes}m"
            hint = "Revisar si cron programado sigue corriendo."
    elif record.status == RuntimeProbeStatus.ERROR:
        note = "Fallo reciente"
        hint = {
            "scraping": "Verificar cookie/Cloudflare y parsing.",
            "telegram": "Verificar bot, chat_id y HTML Telegram.",
            "precheck": "Verificar refresco antes del alert.",
        }.get(name, "Revisar ultimo error.")
    elif record.consecutive_failures:
        tone = RuntimeProbeStatus.WARN.value
        note = f"{record.consecutive_failures} fallos previos"
        hint = "Conviene revisar tendencia antes del siguiente release."

    return {
        "key": name,
        "label": name.capitalize(),
        "status": tone,
        "note": note,
        "hint": hint,
        "last_attempt_at": record.last_attempt_at.isoformat() if record.last_attempt_at else None,
        "last_success_at": record.last_success_at.isoformat() if record.last_success_at else None,
        "last_error_at": record.last_error_at.isoformat() if record.last_error_at else None,
        "last_error_message": record.last_error_message,
        "consecutive_failures": record.consecutive_failures,
    }


def build_observability_diagnostics(cards: list[dict[str, object]], generated_at: datetime) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    for item in cards:
        last_attempt_at = item.get("last_attempt_at")
        stale_minutes = None
        if last_attempt_at:
            stale_minutes = max(0, int((generated_at - datetime.fromisoformat(str(last_attempt_at))).total_seconds() // 60))
        diagnostics.append(
            {
                **item,
                "summary": (
                    item["last_error_message"]
                    or item["hint"]
                    or "Sin diagnostico."
                ),
                "stale_minutes": stale_minutes,
            }
        )
    return diagnostics


def build_risk_blocks(policy: AlertPolicy, schedules: list) -> list[dict[str, object]]:  # noqa: ANN401
    rows: list[dict[str, object]] = []
    for schedule in sorted(
        schedules,
        key=lambda item: (
            item.alert.scheduled_for,
            item.event.scheduled_at or item.alert.scheduled_for,
            item.event.currency,
            item.event.title,
        ),
    ):
        scheduled_at = schedule.event.scheduled_at or schedule.alert.scheduled_for
        risk_start = scheduled_at - policy.risk_before_delta
        risk_end = scheduled_at + policy.risk_after_delta
        row = {
            "event_id": schedule.event.id,
            "title": schedule.event.title,
            "currency": schedule.event.currency,
            "impact": schedule.event.impact.value,
            "scheduled_at": schedule.event.scheduled_at.isoformat() if schedule.event.scheduled_at else None,
            "alert_at": schedule.alert.scheduled_for.isoformat(),
            "risk_window_starts_at": risk_start.isoformat(),
            "risk_window_ends_at": risk_end.isoformat(),
            "is_breaking": schedule.event.is_breaking,
        }
        if rows and risk_start <= rows[-1]["_risk_window_ends_at"]:
            block = rows[-1]
            block["events"].append(row)
            block["event_count"] += 1
            block["currencies"] = sorted({*block["currencies"], row["currency"]})
            block["impacts"] = sorted({*block["impacts"], row["impact"]}, key=impact_rank, reverse=True)
            block["_starts_at"] = min(block["_starts_at"], risk_start)
            block["_risk_window_ends_at"] = max(block["_risk_window_ends_at"], risk_end)
            block["_first_alert_at"] = min(block["_first_alert_at"], schedule.alert.scheduled_for)
            block["_last_event_at"] = max(block["_last_event_at"], scheduled_at)
            if impact_rank(row["impact"]) > impact_rank(block["dominant_impact"]):
                block["dominant_impact"] = row["impact"]
            continue
        rows.append(
            {
                "block_id": f"block-{len(rows) + 1}",
                "_starts_at": risk_start,
                "_risk_window_ends_at": risk_end,
                "_first_alert_at": schedule.alert.scheduled_for,
                "_last_event_at": scheduled_at,
                "dominant_impact": row["impact"],
                "event_count": 1,
                "currencies": [row["currency"]],
                "impacts": [row["impact"]],
                "events": [row],
            }
        )
    return [
        {
            "block_id": block["block_id"],
            "starts_at": block["_starts_at"].isoformat(),
            "ends_at": block["_risk_window_ends_at"].isoformat(),
            "first_alert_at": block["_first_alert_at"].isoformat(),
            "last_event_at": block["_last_event_at"].isoformat(),
            "dominant_impact": block["dominant_impact"],
            "event_count": block["event_count"],
            "currencies": block["currencies"],
            "impacts": block["impacts"],
            "events": block["events"],
        }
        for block in rows[:8]
    ]


def build_automation_summary(
    now: datetime,
    workflow_meta: dict[str, object],
    observability_cards: list[dict[str, object]],
    keepalive_payload: object,
) -> dict[str, object]:
    event_name = workflow_meta.get("event_name")
    keepalive_updated_at = (keepalive_payload or {}).get("updated_at")
    scraping = next((item for item in observability_cards if item["key"] == "scraping"), None)
    telegram = next((item for item in observability_cards if item["key"] == "telegram"), None)
    precheck = next((item for item in observability_cards if item["key"] == "precheck"), None)
    last_successes = [
        item.get("last_success_at")
        for item in [scraping, telegram, precheck]
        if item and item.get("last_success_at")
    ]
    cycle_health = RuntimeProbeStatus.OK.value
    if any(item and item.get("status") == RuntimeProbeStatus.ERROR.value for item in [scraping, telegram, precheck]):
        cycle_health = RuntimeProbeStatus.ERROR.value
    elif any(item and item.get("status") == RuntimeProbeStatus.WARN.value for item in [scraping, telegram, precheck]):
        cycle_health = RuntimeProbeStatus.WARN.value
    return {
        "trigger": event_name,
        "trigger_label": workflow_meta.get("event_label"),
        "actor": workflow_meta.get("actor"),
        "ref_name": workflow_meta.get("ref_name"),
        "run_url": workflow_meta.get("run_url"),
        "run_number": workflow_meta.get("run_number"),
        "cycle_health": cycle_health,
        "last_probe_success_at": max(last_successes) if last_successes else None,
        "keepalive_updated_at": keepalive_updated_at,
        "schedule_confirmed": event_name == "schedule",
        "status_copy": (
            "Ultimo publish vino de cron programado."
            if event_name == "schedule"
            else "Ultimo publish no vino de cron programado."
        ),
        "operator_model": "Superficie unica: operador y admin comparten mismo workflow con gate de environment.",
        "generated_at": now.isoformat(),
    }


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
    observability = RuntimeObservability.model_validate((runtime_payload or {}).get("observability", {}))
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
    impact_breakdown = Counter(item.event.impact.value for item in stored_events)
    currency_breakdown = Counter(item.event.currency for item in stored_events)
    workflow_meta = build_workflow_meta()
    observability_cards = [
        summarize_component("scraping", observability.scraping, now),
        summarize_component("telegram", observability.telegram, now),
        summarize_component("precheck", observability.precheck, now),
    ]
    risk_blocks = build_risk_blocks(policy, schedules)
    observability_diagnostics = build_observability_diagnostics(observability_cards, now)
    automation = build_automation_summary(now, workflow_meta, observability_cards, keepalive_payload)

    return {
        "generated_at": now.isoformat(),
        "workflow": workflow_meta,
        "automation": automation,
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
            "allowed_impacts": [impact.value for impact in policy.allowed_impacts] if policy.allowed_impacts else None,
            "breaking_enabled": policy.breaking_enabled,
            "calendar_enabled": policy.calendar_enabled,
            "monitored_currencies": monitored_currencies,
            "risk_window_before_minutes": policy.risk_window_before_minutes,
            "risk_window_after_minutes": policy.risk_window_after_minutes,
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
        "observability": {
            "cards": observability_cards,
            "diagnostics": observability_diagnostics,
        },
        "dispatch_breakdown": [
            {"kind": kind, "count": count}
            for kind, count in sorted(dispatch_breakdown.items())
        ],
        "impact_breakdown": [
            {"impact": impact, "count": count}
            for impact, count in sorted(impact_breakdown.items())
        ],
        "currency_breakdown": [
            {"currency": currency, "count": count}
            for currency, count in sorted(currency_breakdown.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        "risk_blocks": risk_blocks,
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
