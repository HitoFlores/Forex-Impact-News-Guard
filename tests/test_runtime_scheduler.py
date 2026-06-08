from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import AlertPolicy, ForexEvent, ImpactLevel
from forex_news_guard.domain.runtime import RuntimeProbeStatus
from forex_news_guard.services.runtime_scheduler import RuntimeSchedulerService
from forex_news_guard.storage.event_repository import EventRepository
from forex_news_guard.storage.runtime_repository import RuntimeRepository


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message) -> None:  # noqa: ANN001, ANN201
        self.messages.append(f"{message.title}|{message.body}")


class FailingNotifier(FakeNotifier):
    def send(self, message) -> None:  # noqa: ANN001, ANN201
        raise RuntimeError("telegram down")


class FakeClient:
    def __init__(self, events: list[ForexEvent], refreshed_events: list[ForexEvent] | None = None) -> None:
        self.events = events
        self.refreshed_events = refreshed_events if refreshed_events is not None else events
        self.calls = 0

    def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
        self.calls += 1
        return self.events if self.calls == 1 else self.refreshed_events


class FailingRefreshClient(FakeClient):
    def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
        self.calls += 1
        if self.calls == 1:
            return self.events
        raise RuntimeError("forex factory unavailable")


class FailingClient(FakeClient):
    def __init__(self, error_message: str = "scrape down") -> None:
        self.error_message = error_message
        self.calls = 0

    def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
        self.calls += 1
        raise RuntimeError(self.error_message)


def test_dispatch_due_checks_sends_alert_and_result_once(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 15, 5, tzinfo=timezone)
    event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
        actual="5.25%",
        forecast="5.25%",
        previous="5.25%",
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    event_repository.replace_relevant_events([event], reference_time=now)
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(lead_minutes=5, revalidate_minutes_before_alert=2, result_check_delay_minutes=1),
        client=FakeClient([event]),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    service.run_cycle_at(reference_time=now)
    notifier.messages.clear()
    result = service.dispatch_due_checks_at(reference_time=now)
    second_result = service.dispatch_due_checks_at(reference_time=now)
    observability = runtime_repository.get_observability()

    assert len(result.dispatched) >= 2
    assert len(notifier.messages) >= 2
    assert second_result.dispatched == []
    assert observability.telegram.status == RuntimeProbeStatus.OK
    assert observability.telegram.last_success_at == now


def test_run_cycle_persists_only_relevant_events(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    events = [
        ForexEvent(
            id="usd-high",
            title="FOMC",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
        ),
        ForexEvent(
            id="eur-low",
            title="Survey",
            currency="EUR",
            impact=ImpactLevel.LOW,
            scheduled_at=datetime(2026, 5, 26, 12, 0, tzinfo=timezone),
        ),
    ]
    event_repository = EventRepository(str(tmp_path / "events.db"))
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(allowed_impacts=[ImpactLevel.HIGH], currencies=["USD"]),
        client=FakeClient(events),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    result = service.run_cycle_at(reference_time=now)
    stored = event_repository.list_relevant_events(reference_time=now)
    observability = runtime_repository.get_observability()

    assert len(result.schedules) == 1
    assert len(result.dispatched) == 1
    assert [item.event.id for item in stored] == ["usd-high"]
    assert observability.scraping.status == RuntimeProbeStatus.OK
    assert observability.scraping.last_success_at == now


def test_dispatch_groups_events_with_same_schedule_into_single_message(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 15, 5, tzinfo=timezone)
    events = [
        ForexEvent(
            id="usd-high-1",
            title="FOMC",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
            actual="5.25%",
            forecast="5.25%",
            previous="5.25%",
        ),
        ForexEvent(
            id="usd-high-2",
            title="FOMC Statement",
            currency="USD",
            impact=ImpactLevel.HIGH,
            scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
            actual="N/D",
            forecast="N/D",
            previous="N/D",
        ),
    ]
    event_repository = EventRepository(str(tmp_path / "events.db"))
    event_repository.replace_relevant_events(events, reference_time=now)
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(lead_minutes=5, revalidate_minutes_before_alert=2, result_check_delay_minutes=1),
        client=FakeClient(events),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    service.run_cycle_at(reference_time=now)
    notifier.messages.clear()
    service.dispatch_due_checks_at(reference_time=now)

    assert len(notifier.messages) == 4
    assert "NEWS BLOCK IN 5 MIN" in notifier.messages[0]
    assert "POST-NEWS UPDATE" in notifier.messages[1]


def test_dispatch_due_checks_revalidates_calendar_and_skips_stale_alert(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    sync_time = datetime(2026, 5, 26, 14, 50, tzinfo=timezone)
    dispatch_time = datetime(2026, 5, 26, 14, 55, tzinfo=timezone)
    original_event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    moved_event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 10, tzinfo=timezone),
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    client = FakeClient([original_event], refreshed_events=[moved_event])
    service = RuntimeSchedulerService(
        policy=AlertPolicy(
            lead_minutes=5,
            revalidate_minutes_before_alert=2,
            result_check_delay_minutes=1,
            daily_summary_enabled=False,
        ),
        client=client,
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    service.run_cycle_at(reference_time=sync_time)
    notifier.messages.clear()
    result = service.dispatch_due_checks_at(reference_time=dispatch_time)
    stored = event_repository.list_relevant_events(reference_time=dispatch_time)

    assert client.calls == 2
    assert notifier.messages == []
    assert result.dispatched == []
    assert stored[0].event.scheduled_at == datetime(2026, 5, 26, 15, 10, tzinfo=timezone)


def test_dispatch_due_checks_records_precheck_failure_observability(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    sync_time = datetime(2026, 5, 26, 14, 50, tzinfo=timezone)
    dispatch_time = datetime(2026, 5, 26, 14, 55, tzinfo=timezone)
    event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    client = FailingRefreshClient([event])
    service = RuntimeSchedulerService(
        policy=AlertPolicy(
            lead_minutes=5,
            revalidate_minutes_before_alert=2,
            result_check_delay_minutes=1,
            daily_summary_enabled=False,
        ),
        client=client,
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    service.run_cycle_at(reference_time=sync_time)
    service.dispatch_due_checks_at(reference_time=dispatch_time)
    observability = runtime_repository.get_observability()

    assert observability.precheck.status == RuntimeProbeStatus.ERROR
    assert observability.scraping.status == RuntimeProbeStatus.ERROR
    assert observability.precheck.last_error_message == "RuntimeError: forex factory unavailable"


def test_run_cycle_records_scraping_failure(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    service = RuntimeSchedulerService(
        policy=AlertPolicy(),
        client=FailingClient(),
        event_repository=EventRepository(str(tmp_path / "events.db")),
        runtime_repository=runtime_repository,
        notifier=FakeNotifier(),
    )

    try:
        service.run_cycle_at(reference_time=now)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected run_cycle_at to fail")

    observability = runtime_repository.get_observability()
    assert observability.scraping.status == "error"
    assert observability.scraping.last_error_message == "RuntimeError: scrape down"
    assert observability.scraping.consecutive_failures == 1


def test_dispatch_due_checks_records_precheck_failure(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    sync_time = datetime(2026, 5, 26, 14, 50, tzinfo=timezone)
    dispatch_time = datetime(2026, 5, 26, 14, 55, tzinfo=timezone)
    event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    service = RuntimeSchedulerService(
        policy=AlertPolicy(lead_minutes=5, revalidate_minutes_before_alert=2, daily_summary_enabled=False),
        client=FakeClient([event], refreshed_events=[event]),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=FakeNotifier(),
    )
    service.run_cycle_at(reference_time=sync_time)
    service.client = FailingClient(error_message="precheck miss")

    result = service.dispatch_due_checks_at(reference_time=dispatch_time)

    observability = runtime_repository.get_observability()
    assert "precheck-refresh-failed:1" in result.skipped
    assert observability.precheck.status == "error"
    assert observability.precheck.last_error_message == "RuntimeError: precheck miss"


def test_dispatch_due_checks_records_telegram_failure(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 15, 5, tzinfo=timezone)
    event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    event_repository.replace_relevant_events([event], reference_time=now)
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    service = RuntimeSchedulerService(
        policy=AlertPolicy(lead_minutes=5, revalidate_minutes_before_alert=2, daily_summary_enabled=False),
        client=FakeClient([event]),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=FailingNotifier(),
    )

    try:
        service.dispatch_due_checks_at(reference_time=now)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected dispatch_due_checks_at to fail")

    observability = runtime_repository.get_observability()
    assert observability.telegram.status == "error"
    assert observability.telegram.last_error_message == "RuntimeError: telegram down"
