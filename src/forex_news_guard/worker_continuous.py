import logging
import time

from forex_news_guard.services.runtime_scheduler import RuntimeSchedulerService


logger = logging.getLogger(__name__)


def _wait_forever() -> None:
    while True:
        time.sleep(3600)


def run_worker_continuous() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    service = RuntimeSchedulerService()
    logger.info("Continuous worker starting")
    service.start()
    try:
        _wait_forever()
    except KeyboardInterrupt:
        logger.info("Continuous worker stopping")
    finally:
        service.shutdown()


if __name__ == "__main__":
    run_worker_continuous()
