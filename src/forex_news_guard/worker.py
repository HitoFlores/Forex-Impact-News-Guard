import logging

from forex_news_guard.services.runtime_scheduler import RuntimeSchedulerService


logger = logging.getLogger(__name__)


def run_worker() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    service = RuntimeSchedulerService()
    logger.info("Worker started")
    sync_result, dispatch_result = service.run_full_cycle()
    logger.info(
        "Worker completed synced_at=%s sync_dispatches=%s due_dispatches=%s due_skipped=%s",
        sync_result.synced_at.isoformat(),
        len(sync_result.dispatched),
        len(dispatch_result.dispatched),
        len(dispatch_result.skipped),
    )


if __name__ == "__main__":
    run_worker()
