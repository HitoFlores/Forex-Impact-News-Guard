from datetime import datetime
from zoneinfo import ZoneInfo

from forex_news_guard.domain.runtime import RuntimeSyncResult
from forex_news_guard.worker import run_worker
from forex_news_guard.worker_continuous import run_worker_continuous


class FakeSchedulerService:
    def __init__(self) -> None:
        self.called = False

    def run_full_cycle(self) -> tuple[RuntimeSyncResult, RuntimeSyncResult]:
        self.called = True
        now = datetime(2026, 6, 8, 12, 0, tzinfo=ZoneInfo("America/Chihuahua"))
        return (
            RuntimeSyncResult(synced_at=now),
            RuntimeSyncResult(synced_at=now, skipped=["group-alert:demo"]),
        )


class FakeContinuousSchedulerService:
    def __init__(self) -> None:
        self.started = False
        self.shutdown_called = False

    def start(self) -> None:
        self.started = True

    def shutdown(self) -> None:
        self.shutdown_called = True


def test_run_worker_executes_full_cycle(monkeypatch) -> None:  # noqa: ANN001
    fake = FakeSchedulerService()
    monkeypatch.setattr("forex_news_guard.worker.RuntimeSchedulerService", lambda: fake)

    run_worker()

    assert fake.called is True


def test_run_worker_continuous_starts_and_shutdowns_on_interrupt(monkeypatch) -> None:  # noqa: ANN001
    fake = FakeContinuousSchedulerService()
    monkeypatch.setattr("forex_news_guard.worker_continuous.RuntimeSchedulerService", lambda: fake)

    def interrupt() -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr("forex_news_guard.worker_continuous._wait_forever", interrupt)

    run_worker_continuous()

    assert fake.started is True
    assert fake.shutdown_called is True
