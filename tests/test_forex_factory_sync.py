from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import AlertPolicy, ForexEvent, ImpactLevel
from forex_news_guard.services.forex_factory_monitor import sync_relevant_calendar_events
from forex_news_guard.storage.event_repository import EventRepository


def test_sync_relevant_calendar_events_persists_and_schedules(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    reference_time = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    repository = EventRepository(str(tmp_path / "events.db"))

    class FakeClient:
        def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
            return [
                ForexEvent(
                    id="usd-high",
                    title="FOMC",
                    currency="USD",
                    impact=ImpactLevel.HIGH,
                    scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
                    actual="",
                    forecast="5.25%",
                    previous="5.25%",
                    actual_better_worse=1,
                ),
                ForexEvent(
                    id="eur-low",
                    title="Survey",
                    currency="EUR",
                    impact=ImpactLevel.LOW,
                    scheduled_at=datetime(2026, 5, 26, 12, 0, tzinfo=timezone),
                ),
                ForexEvent(
                    id="usd-tomorrow",
                    title="GDP",
                    currency="USD",
                    impact=ImpactLevel.HIGH,
                    scheduled_at=datetime(2026, 5, 27, 9, 0, tzinfo=timezone),
                ),
                ForexEvent(
                    id="usd-future",
                    title="PCE",
                    currency="USD",
                    impact=ImpactLevel.HIGH,
                    scheduled_at=datetime(2026, 5, 28, 9, 0, tzinfo=timezone),
                ),
            ]

    stored_events, schedules = sync_relevant_calendar_events(
        policy=AlertPolicy(allowed_impacts=[ImpactLevel.HIGH], currencies=["USD"]),
        reference_time=reference_time,
        client=FakeClient(),
        repository=repository,
    )

    assert [item.event.id for item in stored_events] == ["usd-high", "usd-tomorrow"]
    assert [item.event.id for item in schedules] == ["usd-high", "usd-tomorrow"]
    assert schedules[0].event.forecast == "5.25%"
