from datetime import datetime, timedelta

from forex_news_guard.core.config import get_settings
from forex_news_guard.domain.models import AlertPolicy, ForexEvent, ImpactLevel, TelegramSmokeTestResponse
from forex_news_guard.services.notification_formatter import (
    build_daily_summary_message,
    build_grouped_pre_alert_message,
    build_grouped_result_message,
    build_pre_alert_message,
    build_result_message,
)
from forex_news_guard.services.settings_service import SettingsService
from forex_news_guard.services.telegram_notifier import TelegramNotifier


def send_telegram_smoke_test(
    policy: AlertPolicy | None = None,
    notifier: TelegramNotifier | None = None,
    reference_time: datetime | None = None,
) -> TelegramSmokeTestResponse:
    settings = get_settings()
    alert_policy = policy or SettingsService().get_policy()
    generated_at = reference_time or datetime.now(tz=alert_policy.timezone_info)
    sender = notifier or _build_notifier(settings.telegram_bot_token, settings.telegram_chat_id, settings.forex_factory_timeout_seconds)

    first_event = ForexEvent(
        id="smoke-usd-cpi",
        title="US CPI m/m",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=generated_at + timedelta(minutes=alert_policy.lead_minutes),
        actual="0.4%",
        forecast="0.3%",
        previous="0.2%",
        actual_better_worse=1,
    )
    second_event = ForexEvent(
        id="smoke-usd-fomc",
        title="FOMC Statement",
        currency="USD",
        impact=ImpactLevel.HIGH,
        scheduled_at=first_event.scheduled_at,
        actual="N/D",
        forecast="N/D",
        previous="N/D",
        actual_better_worse=None,
    )
    third_event = ForexEvent(
        id="smoke-eur-ecb",
        title="ECB Press Conference",
        currency="EUR",
        impact=ImpactLevel.HIGH,
        scheduled_at=generated_at + timedelta(hours=2),
        actual="3.75%",
        forecast="3.75%",
        previous="4.00%",
        actual_better_worse=-1,
    )

    messages = [
        build_daily_summary_message([first_event, third_event], generated_at),
        build_pre_alert_message(third_event, alert_policy.lead_minutes),
        build_grouped_pre_alert_message([first_event, second_event], alert_policy.lead_minutes),
        build_result_message(first_event, generated_at),
        build_grouped_result_message([first_event, third_event], generated_at),
    ]
    sent_messages: list[str] = []
    for message in messages:
        sender.send(message)
        sent_messages.append(message.title)

    return TelegramSmokeTestResponse(sent_messages=sent_messages)


def _build_notifier(bot_token: str | None, chat_id: str | None, timeout_seconds: float) -> TelegramNotifier:
    if not bot_token or not chat_id:
        raise RuntimeError(
            "Configura FOREX_GUARD_TELEGRAM_BOT_TOKEN y FOREX_GUARD_TELEGRAM_CHAT_ID para probar Telegram."
        )
    return TelegramNotifier(bot_token=bot_token, chat_id=chat_id, timeout_seconds=timeout_seconds)
