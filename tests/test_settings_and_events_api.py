from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from forex_news_guard.domain.models import AlertPolicy, ForexEvent, ImpactLevel, StoredEvent
from forex_news_guard.main import app

client = TestClient(app)


def test_settings_endpoints_round_trip() -> None:
    payload = {
        "allowed_impacts": ["high", "medium"],
        "currencies": ["USD", "EUR"],
        "lead_minutes": 9,
        "daily_summary_enabled": False,
        "timezone": "America/Chihuahua",
    }

    put_response = client.put("/api/v1/settings", json=payload)
    get_response = client.get("/api/v1/settings")

    assert put_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["lead_minutes"] == 9
    assert get_response.json()["daily_summary_enabled"] is False


def test_events_endpoints_return_relevant_data() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    stored_events = [
        StoredEvent(
            event=ForexEvent(
                id="usd-high",
                title="FOMC",
                currency="USD",
                impact=ImpactLevel.HIGH,
                scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
            ),
            stored_at=datetime(2026, 5, 26, 10, 0, tzinfo=timezone),
            event_date="2026-05-26",
        )
    ]
    policy = AlertPolicy(allowed_impacts=[ImpactLevel.HIGH], lead_minutes=5, timezone="America/Chihuahua")

    with patch("forex_news_guard.api.routes.events.EventRepository") as repo_cls:
        repo_cls.return_value.list_relevant_events.return_value = stored_events
        with patch("forex_news_guard.api.routes.events.SettingsService") as settings_cls:
            settings_cls.return_value.get_policy.return_value = policy
            events_response = client.get("/api/v1/events/relevant")
            schedules_response = client.get("/api/v1/events/schedules/upcoming")

    assert events_response.status_code == 200
    assert schedules_response.status_code == 200
    assert events_response.json()[0]["event"]["id"] == "usd-high"
    assert schedules_response.json()[0]["event"]["id"] == "usd-high"
    assert schedules_response.json()[0]["alert"]["scheduled_for"] == "2026-05-26T14:55:00-06:00"
