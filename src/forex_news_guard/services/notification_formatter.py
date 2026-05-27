from datetime import datetime
from html import escape

from forex_news_guard.domain.models import EventSchedule, ForexEvent, ImpactLevel
from forex_news_guard.domain.runtime import NotificationMessage


def build_pre_alert_message(event: ForexEvent, lead_minutes: int) -> NotificationMessage:
    event_time = event.scheduled_at.strftime("%H:%M") if event.scheduled_at else "N/D"
    flag = _currency_flag(event.currency)
    impact_badge = _impact_badge(event.impact)
    return NotificationMessage(
        event_id=event.id,
        impact=event.impact,
        title="FOREX IMPACT ALERT",
        body=(
            f"<blockquote><b>⏰ {escape(event_time)}  {flag} {escape(event.currency)}</b></blockquote>\n"
            f"📰 <b>{escape(event.title)}</b>\n"
            f"📊 <code>Impacto  :</code> {impact_badge} <b>{escape(_impact_label(event.impact))}</b>\n"
            f"🛑 <code>Accion   :</code> Stop trading window in <b>{lead_minutes} min</b>\n"
            f"🛡️ <code>Estado   :</code> Pre-news protection"
        ),
    )


def build_result_message(event: ForexEvent, checked_at: datetime) -> NotificationMessage:
    actual = event.actual or "N/D"
    forecast = event.forecast or "N/D"
    previous = event.previous or "N/D"
    flag = _currency_flag(event.currency)
    impact_badge = _impact_badge(event.impact)
    result_badge = _result_badge(event.actual_better_worse)
    return NotificationMessage(
        event_id=event.id,
        impact=event.impact,
        title="FOREX RESULT UPDATE",
        body=(
            f"<blockquote><b>📣 {flag} {escape(event.currency)}  {escape(checked_at.strftime('%H:%M'))}</b></blockquote>\n"
            f"📰 <b>{escape(event.title)}</b>\n"
            f"📊 <code>Impacto  :</code> {impact_badge} <b>{escape(_impact_label(event.impact))}</b>\n"
            f"{result_badge} <code>Actual   :</code> <b>{escape(actual)}</b>\n"
            f"🎯 <code>Forecast :</code> <code>{escape(forecast)}</code>\n"
            f"🗂️ <code>Previous :</code> <code>{escape(previous)}</code>"
        ),
    )


def build_daily_summary_message(events: list[ForexEvent], generated_at: datetime) -> NotificationMessage:
    if not events:
        body = "<i>No hay noticias relevantes configuradas para hoy.</i>"
    else:
        lines = ["<b>HIGH IMPACT CALENDAR</b>", f"<i>{escape(generated_at.strftime('%Y-%m-%d'))}</i>", ""]
        for event in events:
            event_time = event.scheduled_at.strftime("%H:%M") if event.scheduled_at else "N/D"
            flag = _currency_flag(event.currency)
            impact_badge = _impact_badge(event.impact)
            lines.append(
                f"⏰ <b>{escape(event_time)}  {flag} {escape(event.currency)}</b>\n"
                f"📰 {escape(event.title)}\n"
                f"📊 <code>Impacto:</code> {impact_badge} <b>{escape(_impact_label(event.impact))}</b>\n"
            )
        body = "\n".join(lines)
    return NotificationMessage(
        event_id=f"daily-summary-{generated_at.date().isoformat()}",
        impact=ImpactLevel.HIGH,
        title="FOREX FACTORY DAILY",
        body=body,
    )


def build_grouped_pre_alert_message(events: list[ForexEvent], lead_minutes: int) -> NotificationMessage:
    primary = events[0]
    event_time = primary.scheduled_at.strftime("%H:%M") if primary.scheduled_at else "N/D"
    lines = [
        f"🚨 <b>NEWS BLOCK IN {lead_minutes} MIN</b>",
        f"⏰ <i>{escape(event_time)}</i>",
        "",
    ]
    for event in events:
        flag = _currency_flag(event.currency)
        impact_badge = _impact_badge(event.impact)
        lines.append(
            f"{flag} <b>{escape(event.currency)}</b>  {escape(event.title)}\n"
            f"📊 <code>Impacto:</code> {impact_badge} <b>{escape(_impact_label(event.impact))}</b>\n"
        )
    return NotificationMessage(
        event_id=primary.id,
        impact=primary.impact,
        title="FOREX IMPACT ALERT",
        body="\n".join(lines),
    )


def build_grouped_result_message(events: list[ForexEvent], checked_at: datetime) -> NotificationMessage:
    primary = events[0]
    lines = [
        "📣 <b>POST-NEWS UPDATE</b>",
        f"⏰ <i>{escape(checked_at.strftime('%H:%M'))}</i>",
        "",
    ]
    for event in events:
        flag = _currency_flag(event.currency)
        result_badge = _result_badge(event.actual_better_worse)
        lines.append(
            f"{flag} <b>{escape(event.currency)}</b>  {escape(event.title)}\n"
            f"{result_badge} <code>Actual   :</code> <b>{escape(event.actual or 'N/D')}</b>\n"
            f"🎯 <code>Forecast :</code> <code>{escape(event.forecast or 'N/D')}</code>\n"
            f"🗂️ <code>Previous :</code> <code>{escape(event.previous or 'N/D')}</code>\n"
        )
    return NotificationMessage(
        event_id=primary.id,
        impact=primary.impact,
        title="FOREX RESULT UPDATE",
        body="\n".join(lines),
    )


def build_schedule_summary(schedule: EventSchedule) -> str:
    return (
        f"{schedule.event.id} | "
        f"precheck={schedule.precheck.scheduled_for.isoformat()} | "
        f"alert={schedule.alert.scheduled_for.isoformat()} | "
        f"results={len(schedule.result_checks)}"
    )


def _impact_label(impact: ImpactLevel) -> str:
    return {
        ImpactLevel.HIGH: "Muy Alto",
        ImpactLevel.MEDIUM: "Medio",
        ImpactLevel.LOW: "Bajo",
    }[impact]


def _currency_flag(currency: str) -> str:
    return {
        "AUD": "🇦🇺",
        "CAD": "🇨🇦",
        "CHF": "🇨🇭",
        "CNY": "🇨🇳",
        "EUR": "🇪🇺",
        "GBP": "🇬🇧",
        "JPY": "🇯🇵",
        "MXN": "🇲🇽",
        "NZD": "🇳🇿",
        "USD": "🇺🇸",
    }.get(currency.upper(), "🏳️")


def _impact_badge(impact: ImpactLevel) -> str:
    return {
        ImpactLevel.HIGH: "🔴",
        ImpactLevel.MEDIUM: "🟠",
        ImpactLevel.LOW: "🟡",
    }[impact]


def _result_badge(actual_better_worse: int | None) -> str:
    if actual_better_worse is None:
        return "⚪"
    if actual_better_worse > 0:
        return "🟢"
    if actual_better_worse < 0:
        return "🔴"
    return "⚪"
