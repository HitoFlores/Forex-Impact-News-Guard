from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import ForexEvent, ImpactLevel
from forex_news_guard.services.notification_formatter import build_daily_summary_message


def test_daily_summary_lists_today_events_and_only_mentions_tomorrow() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    generated_at = datetime(2026, 5, 26, 8, 0, tzinfo=timezone)
    today_event = ForexEvent(
        id="today",
        title="FOMC Meeting Minutes",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=generated_at.replace(hour=12),
    )
    tomorrow_event = ForexEvent(
        id="tomorrow",
        title="GDP q/q",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=(generated_at + timedelta(days=1)).replace(hour=9),
    )

    message = build_daily_summary_message([today_event, tomorrow_event], generated_at)

    assert "FOMC Meeting Minutes" in message.body
    assert "GDP q/q" not in message.body
    assert "Manana se esperan 1 noticia de alto impacto." in message.body


def test_daily_summary_no_today_events_still_mentions_tomorrow() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    generated_at = datetime(2026, 5, 26, 8, 0, tzinfo=timezone)
    tomorrow_event = ForexEvent(
        id="tomorrow",
        title="GDP q/q",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=(generated_at + timedelta(days=1)).replace(hour=9),
    )

    message = build_daily_summary_message([tomorrow_event], generated_at)

    assert "No hay noticias relevantes configuradas para hoy." in message.body
    assert "GDP q/q" not in message.body
    assert "Manana se esperan 1 noticia de alto impacto." in message.body
