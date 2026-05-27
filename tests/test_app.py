from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from forex_news_guard.integrations.forex_factory import ForexFactoryBlockedError
from forex_news_guard.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_alert_preview_endpoint() -> None:
    response = client.post(
        "/api/v1/alerts/preview",
        json={
            "generated_at": "2026-05-26T15:00:00-07:00",
            "policy": {
                "lead_minutes": 10,
                "risk_window_before_minutes": 20,
                "risk_window_after_minutes": 15,
                "timezone": "America/Chihuahua",
            },
            "events": [
                {
                    "id": "fed-1",
                    "title": "FOMC Rate Decision",
                    "currency": "USD",
                    "impact": "high",
                    "scheduled_at": "2026-05-26T16:00:00-07:00",
                    "url": "https://www.forexfactory.com/",
                },
                {
                    "id": "headline-1",
                    "title": "Unexpected emergency meeting",
                    "currency": "USD",
                    "impact": "high",
                    "is_breaking": True,
                    "published_at": "2026-05-26T15:00:00-07:00",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generated_at"] == "2026-05-26T15:00:00-07:00"
    assert len(body["planned_alerts"]) == 2
    assert len(body["risk_windows"]) == 1


def test_forex_factory_live_preview_endpoint_handles_upstream_block() -> None:
    with patch(
        "forex_news_guard.api.routes.alerts.preview_live_alerts",
        side_effect=ForexFactoryBlockedError("Forex Factory blocked"),
    ):
        response = client.post("/api/v1/alerts/forex-factory/live-preview")

    assert response.status_code == 502
