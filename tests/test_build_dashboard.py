from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.build_dashboard import build_dashboard_payload


def test_build_dashboard_payload_adds_ops_summary() -> None:
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
            ]
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
