from datetime import datetime
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import AlertPolicy, ForexEvent, ImpactLevel
from forex_news_guard.services.event_scheduler import build_event_schedules, filter_relevant_events


def test_filter_relevant_events_respects_impacts_and_currencies() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    events = [
        ForexEvent(
            id="usd-high",
            title="FOMC",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 26, 14, 0, tzinfo=timezone),
        ),
        ForexEvent(
            id="eur-medium",
            title="CPI",
            currency="EUR",
            impact=ImpactLevel.MEDIUM,
            scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
        ),
        ForexEvent(
            id="jpy-low",
            title="Survey",
            currency="JPY",
            impact=ImpactLevel.LOW,
            scheduled_at=datetime(2026, 5, 26, 16, 0, tzinfo=timezone),
        ),
    ]
    policy = AlertPolicy(allowed_impacts=[ImpactLevel.HIGH, ImpactLevel.MEDIUM], currencies=["USD", "EUR"])

    filtered = filter_relevant_events(events, policy)

    assert [event.id for event in filtered] == ["usd-high", "eur-medium"]


def test_build_event_schedules_creates_precheck_alert_and_result_retries() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    policy = AlertPolicy(
        lead_minutes=5,
        revalidate_minutes_before_alert=2,
        result_check_delay_minutes=1,
        result_retry_minutes=[3, 5],
    )
    event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )

    schedules = build_event_schedules([event], policy)

    assert len(schedules) == 1
    schedule = schedules[0]
    assert schedule.precheck.scheduled_for == datetime(2026, 5, 26, 14, 53, tzinfo=timezone)
    assert schedule.alert.scheduled_for == datetime(2026, 5, 26, 14, 55, tzinfo=timezone)
    assert [item.scheduled_for for item in schedule.result_checks] == [
        datetime(2026, 5, 26, 15, 1, tzinfo=timezone),
        datetime(2026, 5, 26, 15, 3, tzinfo=timezone),
        datetime(2026, 5, 26, 15, 5, tzinfo=timezone),
    ]
