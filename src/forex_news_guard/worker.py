import logging

from forex_news_guard.services.runtime_scheduler import RuntimeSchedulerService


def run_worker() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    service = RuntimeSchedulerService()
    service.run_once()


if __name__ == "__main__":
    run_worker()
