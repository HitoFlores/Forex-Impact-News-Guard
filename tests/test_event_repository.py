from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import ForexEvent, ImpactLevel
from forex_news_guard.storage.event_repository import EventRepository


def test_repository_retains_only_today_and_tomorrow(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    reference_time = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    repository = EventRepository(str(tmp_path / "events.db"))

    events = [
        ForexEvent(
            id="yesterday",
            title="Old event",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 25, 9, 0, tzinfo=timezone),
        ),
        ForexEvent(
            id="today",
            title="Today event",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 26, 14, 0, tzinfo=timezone),
        ),
        ForexEvent(
            id="tomorrow",
            title="Tomorrow event",
            currency="EUR",
            impact=ImpactLevel.MEDIUM,
            scheduled_at=datetime(2026, 5, 27, 8, 30, tzinfo=timezone),
        ),
        ForexEvent(
            id="future",
            title="Future event",
            currency="JPY",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 28, 8, 30, tzinfo=timezone),
        ),
    ]

    repository.replace_relevant_events(events, reference_time=reference_time)
    stored = repository.list_relevant_events(reference_time=reference_time)

    assert [item.event.id for item in stored] == ["today", "tomorrow"]


def test_repository_cleanup_removes_old_rows_after_day_rollover(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    repository = EventRepository(str(tmp_path / "events.db"))
    first_reference = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    second_reference = datetime(2026, 5, 27, 10, 0, tzinfo=timezone)

    repository.replace_relevant_events(
        [
            ForexEvent(
                id="today",
                title="Today event",
                currency="USD",
                impact=ImpactLevel.HIGH,
                scheduled_at=datetime(2026, 5, 26, 14, 0, tzinfo=timezone),
            ),
            ForexEvent(
                id="tomorrow",
                title="Tomorrow event",
                currency="USD",
                impact=ImpactLevel.HIGH,
                scheduled_at=datetime(2026, 5, 27, 14, 0, tzinfo=timezone),
            ),
        ],
        reference_time=first_reference,
    )
    repository.cleanup(reference_time=second_reference)
    stored = repository.list_relevant_events(reference_time=second_reference)

    assert [item.event.id for item in stored] == ["tomorrow"]
