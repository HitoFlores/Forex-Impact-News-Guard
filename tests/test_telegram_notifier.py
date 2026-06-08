import httpx
import pytest

from forex_news_guard.domain.models import ImpactLevel
from forex_news_guard.domain.runtime import NotificationMessage
from forex_news_guard.services.telegram_notifier import TelegramNotifier


def test_telegram_notifier_trims_bot_token_and_chat_id() -> None:
    notifier = TelegramNotifier(bot_token="  token  ", chat_id="  -100123  ")

    assert notifier.bot_token == "token"
    assert notifier.chat_id == "-100123"


def test_telegram_notifier_raises_error_with_telegram_detail(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(self, url: str, json: dict[str, str]) -> httpx.Response:  # noqa: ANN001
        request = httpx.Request("POST", url, json=json)
        return httpx.Response(
            400,
            request=request,
            json={"ok": False, "error_code": 400, "description": "Bad Request: chat not found"},
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    notifier = TelegramNotifier(bot_token="token", chat_id="-100123")

    with pytest.raises(RuntimeError, match="chat not found"):
        notifier.send(
            NotificationMessage(
                title="FOREX FACTORY DAILY",
                body="ping",
                event_id="test-event",
                impact=ImpactLevel.HIGH,
            )
        )
