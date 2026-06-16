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
    def __init__(
        self,
        events: list[ForexEvent],
        refreshed_events: list[ForexEvent] | None = None,
        breaking_events: list[ForexEvent] | None = None,
    ) -> None:
        self.events = events
        self.refreshed_events = refreshed_events if refreshed_events is not None else events
        self.breaking_events = breaking_events or []
        self.calls = 0
        self.breaking_calls = 0

    def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
        self.calls += 1
        return self.events if self.calls == 1 else self.refreshed_events

    def fetch_breaking_news_events(self, reference_time: datetime):  # noqa: ANN202
        self.breaking_calls += 1
        return self.breaking_events


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


class FakeBackgroundScheduler:
    def __init__(self) -> None:
        self.jobs: list[dict[str, object]] = []
        self.started = False

    def add_job(self, func, trigger: str, **kwargs) -> None:  # noqa: ANN001, ANN202
        self.jobs.append({"func": func, "trigger": trigger, **kwargs})

    def start(self) -> None:
        self.started = True


def test_start_registers_sync_and_dispatch_interval_jobs(tmp_path: Path) -> None:
    service = RuntimeSchedulerService(
        policy=AlertPolicy(),
        client=FakeClient([]),
        event_repository=EventRepository(str(tmp_path / "events.db")),
        runtime_repository=RuntimeRepository(str(tmp_path / "events.db")),
        notifier=FakeNotifier(),
    )
    fake_scheduler = FakeBackgroundScheduler()
    service.scheduler = fake_scheduler

    service.start()

    assert fake_scheduler.started is True
    assert fake_scheduler.jobs == [
        {
            "func": service.run_cycle,
            "trigger": "interval",
            "minutes": 30,
            "id": "sync-relevant-events",
            "replace_existing": True,
        },
        {
            "func": service.dispatch_due_checks,
            "trigger": "interval",
            "seconds": 30,
            "id": "dispatch-due-checks",
            "replace_existing": True,
        },
    ]


def test_dispatch_due_checks_sends_alert_once_inside_timing_window(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 14, 55, tzinfo=timezone)
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

    assert len(result.dispatched) == 2
    assert len(notifier.messages) == 1
    assert "Stop trading window in <b>5 min</b>" in notifier.messages[0]
    assert second_result.dispatched == []
    assert observability.telegram.status == RuntimeProbeStatus.OK
    assert observability.telegram.last_success_at == now


def test_dispatch_due_checks_sends_final_result_once_across_due_retries(tmp_path: Path) -> None:
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

    result = service.dispatch_due_checks_at(reference_time=now)
    second_result = service.dispatch_due_checks_at(reference_time=now)

    assert len(notifier.messages) == 1
    assert "FOREX RESULT UPDATE" in notifier.messages[0]
    assert "15:00" in notifier.messages[0]
    result_dispatches = [record for record in result.dispatched if record.kind.value == "result"]
    assert [record.attempt for record in result_dispatches] == [1]
    assert second_result.dispatched == []


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
        policy=AlertPolicy(allowed_impacts=[ImpactLevel.HIGH], currencies=["USD"], daily_summary_enabled=False),
        client=FakeClient(events),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    result = service.run_cycle_at(reference_time=now)
    stored = event_repository.list_relevant_events(reference_time=now)
    observability = runtime_repository.get_observability()

    assert len(result.schedules) == 1
    assert [record for record in result.dispatched if record.kind.value == "result"] == []
    assert [item.event.id for item in stored] == ["usd-high"]
    assert observability.scraping.status == RuntimeProbeStatus.OK
    assert observability.scraping.last_success_at == now


def test_run_cycle_includes_breaking_news_when_enabled(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    calendar_event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    breaking_event = ForexEvent(
        id="breaking-fed",
        title="Fed announces emergency statement",
        currency="USD",
        impact=ImpactLevel.HIGH,
        published_at=now,
        is_breaking=True,
    )
    client = FakeClient([calendar_event], breaking_events=[breaking_event])
    event_repository = EventRepository(str(tmp_path / "events.db"))
    service = RuntimeSchedulerService(
        policy=AlertPolicy(lead_minutes=5, breaking_enabled=True, daily_summary_enabled=False),
        client=client,
        event_repository=event_repository,
        runtime_repository=RuntimeRepository(str(tmp_path / "events.db")),
        notifier=FakeNotifier(),
    )

    result = service.run_cycle_at(reference_time=now)
    stored = event_repository.list_relevant_events(reference_time=now)

    assert client.breaking_calls == 1
    assert [item.event.id for item in stored] == ["breaking-fed", "usd-high"]
    assert any(schedule.event.id == "breaking-fed" and schedule.alert.scheduled_for == now for schedule in result.schedules)


def test_run_cycle_skips_breaking_news_when_disabled(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    event = ForexEvent(
        id="usd-high",
        title="FOMC",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    client = FakeClient([event], breaking_events=[event])
    service = RuntimeSchedulerService(
        policy=AlertPolicy(breaking_enabled=False, daily_summary_enabled=False),
        client=client,
        event_repository=EventRepository(str(tmp_path / "events.db")),
        runtime_repository=RuntimeRepository(str(tmp_path / "events.db")),
        notifier=FakeNotifier(),
    )

    service.run_cycle_at(reference_time=now)

    assert client.breaking_calls == 0


def test_run_cycle_deduplicates_calendar_and_breaking_by_event_id(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    calendar_event = ForexEvent(
        id="shared",
        title="Calendar title",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 5, 26, 15, 0, tzinfo=timezone),
    )
    breaking_event = ForexEvent(
        id="shared",
        title="Breaking title",
        currency="USD",
        impact=ImpactLevel.HIGH,
        published_at=now,
        is_breaking=True,
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    service = RuntimeSchedulerService(
        policy=AlertPolicy(lead_minutes=5, breaking_enabled=True, daily_summary_enabled=False),
        client=FakeClient([calendar_event], breaking_events=[breaking_event]),
        event_repository=event_repository,
        runtime_repository=RuntimeRepository(str(tmp_path / "events.db")),
        notifier=FakeNotifier(),
    )

    service.run_cycle_at(reference_time=now)
    stored = event_repository.list_relevant_events(reference_time=now)

    assert [item.event.id for item in stored] == ["shared"]
    assert stored[0].event.title == "Breaking title"


def test_run_cycle_sends_daily_summary_inside_midnight_window(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 6, 15, 0, 5, tzinfo=timezone)
    event = ForexEvent(
        id="jpy-high",
        title="BOJ Policy Rate",
        currency="JPY",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 6, 15, 20, 30, tzinfo=timezone),
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(daily_summary_enabled=True),
        client=FakeClient([event]),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    result = service.run_cycle_at(reference_time=now)

    assert len(result.dispatched) == 1
    assert result.dispatched[0].event_id == "daily-summary-2026-06-15"
    assert "FOREX FACTORY DAILY" in notifier.messages[0]


def test_run_cycle_skips_stale_daily_summary_after_midnight_window(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 6, 15, 4, 28, tzinfo=timezone)
    event = ForexEvent(
        id="jpy-high",
        title="BOJ Policy Rate",
        currency="JPY",
        impact=ImpactLevel.HIGH,
        scheduled_at=datetime(2026, 6, 15, 20, 30, tzinfo=timezone),
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(daily_summary_enabled=True),
        client=FakeClient([event]),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    result = service.run_cycle_at(reference_time=now)

    assert [record for record in result.dispatched if record.kind.value == "result"] == []
    assert notifier.messages == []


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

    assert len(notifier.messages) == 1
    assert "FOREX RESULT UPDATE" in notifier.messages[0]
    assert "FOMC Statement" not in notifier.messages[0]


def test_dispatch_due_checks_skips_result_retries_without_actual_value(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 6, 15, 4, 28, tzinfo=timezone)
    event = ForexEvent(
        id="eur-medium",
        title="ECB President Lagarde Speaks",
        currency="EUR",
        impact=ImpactLevel.MEDIUM,
        scheduled_at=datetime(2026, 6, 15, 1, 30, tzinfo=timezone),
        actual="N/D",
        forecast="N/D",
        previous="N/D",
    )
    event_repository = EventRepository(str(tmp_path / "events.db"))
    event_repository.replace_relevant_events([event], reference_time=now)
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(
            allowed_impacts=[ImpactLevel.MEDIUM],
            lead_minutes=5,
            revalidate_minutes_before_alert=2,
            result_check_delay_minutes=1,
            result_retry_minutes=[3, 5],
            daily_summary_enabled=False,
        ),
        client=FakeClient([event]),
        event_repository=event_repository,
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    result = service.dispatch_due_checks_at(reference_time=now)

    assert [record for record in result.dispatched if record.kind.value == "result"] == []
    assert notifier.messages == []


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
        actual="5.25%",
        forecast="5.25%",
        previous="5.25%",
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
        actual="5.25%",
        forecast="5.25%",
        previous="5.25%",
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

    assert observability.precheck.status == RuntimeProbeStatus.WARN
    assert observability.scraping.status == RuntimeProbeStatus.WARN
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
    assert observability.scraping.status == "warn"
    assert observability.scraping.last_error_message == "RuntimeError: scrape down"
    assert observability.scraping.consecutive_failures == 1


def test_run_cycle_alerts_operator_on_third_scraping_failure(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    runtime_repository = RuntimeRepository(str(tmp_path / "events.db"))
    notifier = FakeNotifier()
    service = RuntimeSchedulerService(
        policy=AlertPolicy(),
        client=FailingClient(),
        event_repository=EventRepository(str(tmp_path / "events.db")),
        runtime_repository=runtime_repository,
        notifier=notifier,
    )

    for offset in range(4):
        try:
            service.run_cycle_at(reference_time=now.replace(minute=offset))
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected run_cycle_at to fail")

    scraping_alerts = [message for message in notifier.messages if "FOREX SCRAPING ERROR" in message]
    observability = runtime_repository.get_observability()
    assert len(scraping_alerts) == 1
    assert "<b>3</b>" in scraping_alerts[0]
    assert observability.scraping.consecutive_failures == 4


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
    assert observability.precheck.status == "warn"
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
        actual="5.25%",
        forecast="5.25%",
        previous="5.25%",
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
    assert observability.telegram.status == "warn"
    assert observability.telegram.last_error_message == "RuntimeError: telegram down"
