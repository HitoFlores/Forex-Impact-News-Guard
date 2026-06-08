from datetime import datetime
from zoneinfo import ZoneInfo

from forex_news_guard.domain.runtime import RuntimeSyncResult
from forex_news_guard.worker import run_worker


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


def test_run_worker_executes_full_cycle(monkeypatch) -> None:  # noqa: ANN001
    fake = FakeSchedulerService()
    monkeypatch.setattr("forex_news_guard.worker.RuntimeSchedulerService", lambda: fake)

    run_worker()

    assert fake.called is True
