from datetime import datetime
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import AlertPolicy, ForexEvent, ImpactLevel
from forex_news_guard.services.alert_planner import preview_alerts


def test_preview_builds_calendar_and_breaking_alerts() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    policy = AlertPolicy(lead_minutes=20, risk_window_before_minutes=30, risk_window_after_minutes=10)
    generated_at = datetime(2026, 5, 26, 15, 0, tzinfo=timezone)
    scheduled_at = datetime(2026, 5, 26, 16, 0, tzinfo=timezone)

    events = [
        ForexEvent(
            id="nfp-1",
            title="Non-Farm Payrolls",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=scheduled_at,
            url="https://www.forexfactory.com/",
        ),
        ForexEvent(
            id="flash-1",
            title="Emergency central bank statement",
            currency="USD",
            impact=ImpactLevel.HIGH,
            is_breaking=True,
            published_at=generated_at,
            url="https://www.forexfactory.com/",
        ),
    ]

    result = preview_alerts(events=events, policy=policy, generated_at=generated_at)

    assert len(result.planned_alerts) == 2
    assert result.planned_alerts[0].event_id == "flash-1"
    assert result.planned_alerts[1].event_id == "nfp-1"
    assert result.planned_alerts[1].alert_at == datetime(2026, 5, 26, 15, 40, tzinfo=timezone)
    assert len(result.risk_windows) == 1
    assert result.risk_windows[0].starts_at == datetime(2026, 5, 26, 15, 30, tzinfo=timezone)
    assert result.risk_windows[0].ends_at == datetime(2026, 5, 26, 16, 10, tzinfo=timezone)


def test_preview_skips_non_high_impact_when_policy_requires_it() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    policy = AlertPolicy()
    generated_at = datetime(2026, 5, 26, 15, 0, tzinfo=timezone)

    events = [
        ForexEvent(
            id="cpi-medium",
            title="CPI revised",
            currency="EUR",
            impact=ImpactLevel.MEDIUM,
            scheduled_at=datetime(2026, 5, 26, 16, 0, tzinfo=timezone),
        )
    ]

    result = preview_alerts(events=events, policy=policy, generated_at=generated_at)

    assert result.planned_alerts == []
    assert result.risk_windows == []
