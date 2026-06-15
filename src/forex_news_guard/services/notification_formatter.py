from datetime import date, datetime
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
    event_time = event.scheduled_at.strftime("%H:%M") if event.scheduled_at else checked_at.strftime("%H:%M")
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
            f"<blockquote><b>📣 {flag} {escape(event.currency)}  {escape(event_time)}</b></blockquote>\n"
            f"📰 <b>{escape(event.title)}</b>\n"
            f"📊 <code>Impacto  :</code> {impact_badge} <b>{escape(_impact_label(event.impact))}</b>\n"
            f"{result_badge} <code>Actual   :</code> <b>{escape(actual)}</b>\n"
            f"🎯 <code>Forecast :</code> <code>{escape(forecast)}</code>\n"
            f"🗂️ <code>Previous :</code> <code>{escape(previous)}</code>"
        ),
    )


def build_daily_summary_message(events: list[ForexEvent], generated_at: datetime) -> NotificationMessage:
    today = generated_at.date()
    tomorrow = date.fromordinal(today.toordinal() + 1)
    todays_events = [event for event in events if _event_local_date(event, generated_at) == today]
    tomorrows_events = [event for event in events if _event_local_date(event, generated_at) == tomorrow]

    if not todays_events:
        body = "<i>No hay noticias relevantes configuradas para hoy.</i>"
    else:
        lines = ["<b>HIGH IMPACT CALENDAR</b>", f"<i>{escape(generated_at.strftime('%Y-%m-%d'))}</i>", ""]
        for event in todays_events:
            event_time = event.scheduled_at.strftime("%H:%M") if event.scheduled_at else "N/D"
            flag = _currency_flag(event.currency)
            impact_badge = _impact_badge(event.impact)
            lines.append(
                f"⏰ <b>{escape(event_time)}  {flag} {escape(event.currency)}</b>\n"
                f"📰 {escape(event.title)}\n"
                f"📊 <code>Impacto:</code> {impact_badge} <b>{escape(_impact_label(event.impact))}</b>\n"
            )
        body = "\n".join(lines)
    if tomorrows_events:
        count = len(tomorrows_events)
        plural = "s" if count != 1 else ""
        body = f"{body}\n\n<i>Manana se esperan {count} noticia{plural} de alto impacto.</i>"
    return NotificationMessage(
        event_id=f"daily-summary-{generated_at.date().isoformat()}",
        impact=ImpactLevel.HIGH,
        title="FOREX FACTORY DAILY",
        body=body,
    )


def build_scraping_failure_message(consecutive_failures: int, error_message: str, checked_at: datetime) -> NotificationMessage:
    return NotificationMessage(
        event_id=f"scraping-failure-{checked_at.date().isoformat()}",
        impact=ImpactLevel.HIGH,
        title="FOREX SCRAPING ERROR",
        body=(
            "<b>Forex Factory scraping is failing</b>\n"
            f"<code>Failures :</code> <b>{consecutive_failures}</b>\n"
            f"<code>Checked  :</code> {escape(checked_at.isoformat())}\n"
            f"<code>Error    :</code> {escape(error_message)}"
        ),
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
    event_time = primary.scheduled_at.strftime("%H:%M") if primary.scheduled_at else checked_at.strftime("%H:%M")
    lines = [
        "📣 <b>POST-NEWS UPDATE</b>",
        f"⏰ <i>{escape(event_time)}</i>",
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


def _event_local_date(event: ForexEvent, generated_at: datetime) -> date | None:
    if event.scheduled_at is None:
        return None
    if generated_at.tzinfo is None:
        return event.scheduled_at.date()
    return event.scheduled_at.astimezone(generated_at.tzinfo).date()


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
