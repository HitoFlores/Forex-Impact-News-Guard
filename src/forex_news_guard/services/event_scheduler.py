from __future__ import annotations

from datetime import datetime, timedelta

from forex_news_guard.domain.models import (
    AlertPolicy,
    EventSchedule,
    ForexEvent,
    ScheduledEventCheck,
    ScheduledEventCheckKind,
)


def filter_relevant_events(events: list[ForexEvent], policy: AlertPolicy) -> list[ForexEvent]:
    allowed_impacts = policy.effective_impacts
    allowed_currencies = policy.normalized_currencies
    filtered: list[ForexEvent] = []
    for event in events:
        if event.scheduled_at is None:
            continue
        if event.impact not in allowed_impacts:
            continue
        if allowed_currencies and not event.is_breaking and event.currency.upper() not in allowed_currencies:
            continue
        filtered.append(event)
    filtered.sort(key=lambda item: item.scheduled_at or datetime.min.replace(tzinfo=policy.timezone_info))
    return filtered


def build_event_schedules(events: list[ForexEvent], policy: AlertPolicy) -> list[EventSchedule]:
    schedules: list[EventSchedule] = []
    for event in filter_relevant_events(events, policy):
        assert event.scheduled_at is not None
        alert_at = event.scheduled_at - policy.lead_delta
        precheck_at = alert_at - policy.revalidate_delta
        result_checks: list[ScheduledEventCheck] = []
        if policy.include_results:
            result_checks.append(
                ScheduledEventCheck(
                    event_id=event.id,
                    kind=ScheduledEventCheckKind.RESULT,
                    scheduled_for=event.scheduled_at + policy.result_check_delta,
                    attempt=1,
                )
            )
            for attempt, minute_offset in enumerate(policy.result_retry_minutes, start=2):
                result_checks.append(
                    ScheduledEventCheck(
                        event_id=event.id,
                        kind=ScheduledEventCheckKind.RESULT,
                        scheduled_for=event.scheduled_at + timedelta(minutes=minute_offset),
                        attempt=attempt,
                    )
                )
        schedules.append(
            EventSchedule(
                event=event,
                precheck=ScheduledEventCheck(
                    event_id=event.id,
                    kind=ScheduledEventCheckKind.PRECHECK,
                    scheduled_for=precheck_at,
                ),
                alert=ScheduledEventCheck(
                    event_id=event.id,
                    kind=ScheduledEventCheckKind.ALERT,
                    scheduled_for=alert_at,
                ),
                result_checks=result_checks,
            )
        )
    return schedules
