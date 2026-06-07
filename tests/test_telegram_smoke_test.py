from datetime import datetime
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import AlertPolicy
from forex_news_guard.services.telegram_smoke_test import send_telegram_smoke_test


class FakeNotifier:
    def __init__(self) -> None:
        self.titles: list[str] = []

    def send(self, message) -> None:  # noqa: ANN001, ANN201
        self.titles.append(message.title)


def test_send_telegram_smoke_test_builds_all_message_variants() -> None:
    notifier = FakeNotifier()
    response = send_telegram_smoke_test(
        policy=AlertPolicy(lead_minutes=5, timezone="America/Chihuahua"),
        notifier=notifier,
        reference_time=datetime(2026, 5, 26, 10, 0, tzinfo=ZoneInfo("America/Chihuahua")),
    )

    assert response.sent_messages == [
        "FOREX FACTORY DAILY",
        "FOREX IMPACT ALERT",
        "FOREX IMPACT ALERT",
        "FOREX RESULT UPDATE",
        "FOREX RESULT UPDATE",
    ]
    assert notifier.titles == response.sent_messages
