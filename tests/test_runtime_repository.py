from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from forex_news_guard.domain.runtime import (
    AlertDispatchRecord,
    AlertExecutionKind,
    DeliveryChannel,
    RuntimeProbeName,
    RuntimeProbeStatus,
)
from forex_news_guard.storage.runtime_repository import RuntimeRepository


def test_prune_dispatches_removes_records_older_than_ttl(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    repository = RuntimeRepository(str(tmp_path / "runtime.json"))
    old_record = AlertDispatchRecord(
        event_id="old",
        kind=AlertExecutionKind.ALERT,
        attempt=1,
        scheduled_for=now - timedelta(days=9),
        sent_at=now - timedelta(days=9),
        channel=DeliveryChannel.TELEGRAM,
    )
    fresh_record = AlertDispatchRecord(
        event_id="fresh",
        kind=AlertExecutionKind.ALERT,
        attempt=1,
        scheduled_for=now - timedelta(days=2),
        sent_at=now - timedelta(days=2),
        channel=DeliveryChannel.TELEGRAM,
    )
    repository.record_dispatch(old_record)
    repository.record_dispatch(fresh_record)

    removed = repository.prune_dispatches(reference_time=now, ttl_days=7)

    assert removed == 1
    assert not repository.has_been_dispatched(
        event_id="old",
        kind=AlertExecutionKind.ALERT,
        scheduled_for=old_record.scheduled_for,
    )
    assert repository.has_been_dispatched(
        event_id="fresh",
        kind=AlertExecutionKind.ALERT,
        scheduled_for=fresh_record.scheduled_for,
    )


def test_record_probe_error_warns_before_error_threshold_and_success_resets(tmp_path: Path) -> None:
    timezone = ZoneInfo("America/Chihuahua")
    now = datetime(2026, 5, 26, 10, 0, tzinfo=timezone)
    repository = RuntimeRepository(str(tmp_path / "runtime.json"))

    repository.record_probe_error(RuntimeProbeName.SCRAPING, now, "first")
    first = repository.get_observability().scraping
    repository.record_probe_error(RuntimeProbeName.SCRAPING, now + timedelta(minutes=1), "second")
    second = repository.get_observability().scraping
    repository.record_probe_error(RuntimeProbeName.SCRAPING, now + timedelta(minutes=2), "third")
    third = repository.get_observability().scraping
    repository.record_probe_success(RuntimeProbeName.SCRAPING, now + timedelta(minutes=3))
    recovered = repository.get_observability().scraping

    assert first.status == RuntimeProbeStatus.WARN
    assert first.consecutive_failures == 1
    assert second.status == RuntimeProbeStatus.WARN
    assert second.consecutive_failures == 2
    assert third.status == RuntimeProbeStatus.ERROR
    assert third.consecutive_failures == 3
    assert recovered.status == RuntimeProbeStatus.OK
    assert recovered.consecutive_failures == 0
