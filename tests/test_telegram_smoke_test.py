from datetime import datetime
from zoneinfo import ZoneInfo

from forex_news_guard.domain.models import AlertPolicy
from forex_news_guard.services.telegram_smoke_test import _build_notifier, send_telegram_smoke_test


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


def test_build_notifier_prefers_smoke_chat_id() -> None:
    notifier = _build_notifier(
        bot_token="token",
        smoke_chat_id="private-chat",
        default_chat_id="group-chat",
        timeout_seconds=20.0,
    )

    assert notifier.chat_id == "private-chat"


def test_build_notifier_falls_back_to_default_chat_id() -> None:
    notifier = _build_notifier(
        bot_token="token",
        smoke_chat_id=None,
        default_chat_id="group-chat",
        timeout_seconds=20.0,
    )

    assert notifier.chat_id == "group-chat"
