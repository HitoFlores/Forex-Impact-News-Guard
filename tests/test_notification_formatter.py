from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import EventSchedule, ForexEvent, ImpactLevel, ScheduledEventCheck, ScheduledEventCheckKind
from forex_news_guard.services.notification_formatter import (
    build_daily_summary_message,
    build_grouped_pre_alert_message,
    build_grouped_result_message,
    build_pre_alert_message,
    build_result_message,
    build_schedule_summary,
)


def _event(**overrides) -> ForexEvent:  # noqa: ANN003
    timezone = ZoneInfo("America/Chihuahua")
    data = {
        "id": "usd-cpi",
        "title": "CPI m/m",
        "currency": "USD",
        "impact": ImpactLevel.HIGH,
        "scheduled_at": datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
        "actual": "0.3%",
        "forecast": "0.2%",
        "previous": "0.1%",
        "actual_better_worse": 1,
    }
    data.update(overrides)
    return ForexEvent(**data)


def test_build_pre_alert_message_contains_contract_and_escapes_html() -> None:
    event = _event(id="malicious", title="<b>CPI & Jobs</b>", currency="USD")

    message = build_pre_alert_message(event, lead_minutes=5)

    assert message.title == "FOREX IMPACT ALERT"
    assert message.event_id == "malicious"
    assert message.impact == ImpactLevel.HIGH
    assert message.parse_mode == "HTML"
    assert "15:00" in message.body
    assert "USD" in message.body
    assert "&lt;b&gt;CPI &amp; Jobs&lt;/b&gt;" in message.body
    assert "Impacto" in message.body
    assert "Muy Alto" in message.body
    assert "Stop trading window in <b>5 min</b>" in message.body


def test_build_result_message_contains_actual_forecast_previous_and_fallbacks() -> None:
    event = _event(actual=None, forecast=None, previous=None)
    checked_at = datetime(2026, 5, 26, 15, 2, tzinfo=ZoneInfo("America/Chihuahua"))

    message = build_result_message(event, checked_at)

    assert message.title == "FOREX RESULT UPDATE"
    assert message.event_id == "usd-cpi"
    assert message.impact == ImpactLevel.HIGH
    assert message.parse_mode == "HTML"
    assert "CPI m/m" in message.body
    assert "USD" in message.body
    assert "Actual" in message.body
    assert "Forecast" in message.body
    assert "Previous" in message.body
    assert message.body.count("N/D") == 3


def test_build_grouped_pre_alert_message_lists_each_event() -> None:
    events = [
        _event(id="usd-cpi", title="CPI m/m", currency="USD"),
        _event(id="eur-rate", title="ECB Rate", currency="EUR", impact=ImpactLevel.MEDIUM),
    ]

    message = build_grouped_pre_alert_message(events, lead_minutes=10)

    assert message.title == "FOREX IMPACT ALERT"
    assert message.event_id == "usd-cpi"
    assert message.impact == ImpactLevel.HIGH
    assert message.parse_mode == "HTML"
    assert "NEWS BLOCK IN 10 MIN" in message.body
    assert "CPI m/m" in message.body
    assert "ECB Rate" in message.body
    assert "USD" in message.body
    assert "EUR" in message.body
    assert "Muy Alto" in message.body
    assert "Medio" in message.body


def test_build_grouped_result_message_lists_each_event_values() -> None:
    events = [
        _event(id="usd-cpi", title="CPI m/m", currency="USD"),
        _event(id="eur-rate", title="ECB Rate", currency="EUR", actual=None, forecast=None, previous="1.0%"),
    ]
    checked_at = datetime(2026, 5, 26, 15, 2, tzinfo=ZoneInfo("America/Chihuahua"))

    message = build_grouped_result_message(events, checked_at)

    assert message.title == "FOREX RESULT UPDATE"
    assert message.event_id == "usd-cpi"
    assert message.impact == ImpactLevel.HIGH
    assert message.parse_mode == "HTML"
    assert "POST-NEWS UPDATE" in message.body
    assert "CPI m/m" in message.body
    assert "ECB Rate" in message.body
    assert "0.3%" in message.body
    assert "0.2%" in message.body
    assert "0.1%" in message.body
    assert "1.0%" in message.body
    assert message.body.count("N/D") == 2


def test_build_daily_summary_lists_today_events_and_only_mentions_tomorrow() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    generated_at = datetime(2026, 5, 26, 8, 0, tzinfo=timezone)
    today_event = _event(id="today", title="FOMC Meeting Minutes", scheduled_at=generated_at.replace(hour=12))
    tomorrow_event = _event(
        id="tomorrow",
        title="GDP q/q",
        scheduled_at=(generated_at + timedelta(days=1)).replace(hour=9),
    )

    message = build_daily_summary_message([today_event, tomorrow_event], generated_at)

    assert message.title == "FOREX FACTORY DAILY"
    assert message.event_id == "daily-summary-2026-05-26"
    assert message.impact == ImpactLevel.HIGH
    assert message.parse_mode == "HTML"
    assert "FOMC Meeting Minutes" in message.body
    assert "USD" in message.body
    assert "GDP q/q" not in message.body
    assert "Manana se esperan 1 noticia de alto impacto." in message.body


def test_daily_summary_no_today_events_still_mentions_tomorrow() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    generated_at = datetime(2026, 5, 26, 8, 0, tzinfo=timezone)
    tomorrow_event = _event(
        id="tomorrow",
        title="GDP q/q",
        scheduled_at=(generated_at + timedelta(days=1)).replace(hour=9),
    )

    message = build_daily_summary_message([tomorrow_event], generated_at)

    assert "No hay noticias relevantes configuradas para hoy." in message.body
    assert "GDP q/q" not in message.body
    assert "Manana se esperan 1 noticia de alto impacto." in message.body


def test_build_schedule_summary_includes_event_and_check_counts() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    event = _event()
    schedule = EventSchedule(
        event=event,
        precheck=ScheduledEventCheck(
            event_id=event.id,
            kind=ScheduledEventCheckKind.PRECHECK,
            scheduled_for=datetime(2026, 5, 26, 14, 53, tzinfo=timezone),
        ),
        alert=ScheduledEventCheck(
            event_id=event.id,
            kind=ScheduledEventCheckKind.ALERT,
            scheduled_for=datetime(2026, 5, 26, 14, 55, tzinfo=timezone),
        ),
        result_checks=[
            ScheduledEventCheck(
                event_id=event.id,
                kind=ScheduledEventCheckKind.RESULT,
                scheduled_for=datetime(2026, 5, 26, 15, 1, tzinfo=timezone),
            )
        ],
    )

    summary = build_schedule_summary(schedule)

    assert "usd-cpi" in summary
    assert "precheck=2026-05-26T14:53:00-06:00" in summary
    assert "alert=2026-05-26T14:55:00-06:00" in summary
    assert "results=1" in summary
