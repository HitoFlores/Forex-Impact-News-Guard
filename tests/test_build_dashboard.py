from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.build_dashboard import build_dashboard_payload


def test_build_dashboard_payload_adds_ops_summary(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setenv("GITHUB_EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_WORKFLOW", "sync-and-publish")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "88")
    monkeypatch.setenv("GITHUB_REPOSITORY", "HitoFlores/Forex-Impact-News-Guard")
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_ACTOR", "github-actions[bot]")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    generated_at = datetime(2026, 6, 6, 21, 0, tzinfo=ZoneInfo("America/Chihuahua"))
    payload = build_dashboard_payload(
        {
            "currencies": ["USD", "EUR"],
            "lead_minutes": 10,
            "timezone": "America/Chihuahua",
        },
        {
            "relevant_events": [
                {
                    "event": {
                        "id": "usd-cpi",
                        "title": "US CPI m/m",
                        "currency": "USD",
                        "impact": "high",
                        "scheduled_at": "2026-06-06T21:15:00-06:00",
                        "actual": "0.4%",
                        "forecast": "0.3%",
                        "previous": "0.2%",
                    },
                    "stored_at": "2026-06-06T20:59:00-06:00",
                    "event_date": "2026-06-06",
                }
            ]
        },
        {
            "dispatched_alerts": [
                {
                    "event_id": "daily-summary-2026-06-06",
                    "scheduled_for": "2026-06-06T20:30:00-06:00",
                    "kind": "daily_summary",
                    "attempt": 1,
                    "sent_at": "2026-06-06T20:31:00-06:00",
                    "channel": "telegram",
                }
            ],
            "observability": {
                "scraping": {
                    "status": "ok",
                    "last_attempt_at": "2026-06-06T20:55:00-06:00",
                    "last_success_at": "2026-06-06T20:55:00-06:00",
                    "consecutive_failures": 0,
                },
                "telegram": {
                    "status": "error",
                    "last_attempt_at": "2026-06-06T20:58:00-06:00",
                    "last_success_at": "2026-06-06T20:31:00-06:00",
                    "last_error_at": "2026-06-06T20:58:00-06:00",
                    "last_error_message": "RuntimeError: boom",
                    "consecutive_failures": 2,
                },
                "precheck": {
                    "status": "warn",
                    "consecutive_failures": 0,
                },
            },
        },
        {
            "updated_at": "2026-06-01T03:00:00+00:00",
        },
        generated_at=generated_at,
    )

    assert payload["counts"]["tracked_currencies"] == 2
    assert payload["status"]["next_alert_at"] == "2026-06-06T21:05:00-06:00"
    assert payload["status"]["last_dispatch_at"] == "2026-06-06T20:31:00-06:00"
    assert payload["policy_summary"]["monitored_currencies"] == ["EUR", "USD"]
    assert payload["dispatch_breakdown"] == [{"kind": "daily_summary", "count": 1}]
    assert payload["impact_breakdown"] == [{"impact": "high", "count": 1}]
    assert payload["currency_breakdown"] == [{"currency": "USD", "count": 1}]
    assert payload["next_alerts"][0]["risk_window_starts_at"] == "2026-06-06T21:00:00-06:00"
    assert payload["risk_blocks"][0]["event_count"] == 1
    assert payload["observability"]["cards"][0]["key"] == "scraping"
    assert payload["observability"]["cards"][1]["status"] == "error"
    assert payload["observability"]["diagnostics"][1]["last_error_message"] == "RuntimeError: boom"
    assert payload["observability"]["diagnostics"][1]["summary"] == "RuntimeError: boom"
    assert payload["workflow"]["event_name"] == "schedule"
    assert payload["workflow"]["event_label"] == "Cron GitHub"
    assert payload["workflow"]["run_url"] == "https://github.com/HitoFlores/Forex-Impact-News-Guard/actions/runs/12345"
    assert payload["automation"]["schedule_confirmed"] is True
    assert payload["automation"]["trigger_label"] == "Cron GitHub"
