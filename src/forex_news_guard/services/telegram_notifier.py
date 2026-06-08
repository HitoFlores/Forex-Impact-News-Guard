from __future__ import annotations

import httpx

from forex_news_guard.domain.runtime import NotificationMessage


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout_seconds: float = 20.0) -> None:
        self.bot_token = bot_token.strip()
        self.chat_id = chat_id.strip()
        self.timeout_seconds = timeout_seconds

    def send(self, message: NotificationMessage) -> None:
        text = f"<b>{message.title}</b>\n\n{message.body}"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": message.parse_mode,
                    "disable_web_page_preview": True,
                },
            )
        if response.is_error:
            detail = response.text.strip() or response.reason_phrase
            raise RuntimeError(f"Telegram sendMessage failed ({response.status_code}): {detail}")
