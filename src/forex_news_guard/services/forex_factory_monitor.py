from datetime import datetime

from forex_news_guard.core.config import get_settings
from forex_news_guard.domain.models import AlertPolicy, AlertPreviewResponse, EventSchedule, ForexEvent, StoredEvent
from forex_news_guard.integrations.forex_factory import ForexFactoryClient
from forex_news_guard.services.alert_planner import preview_alerts
from forex_news_guard.services.event_scheduler import build_event_schedules, filter_relevant_events
from forex_news_guard.storage.event_repository import EventRepository


def preview_live_alerts(
    policy: AlertPolicy | dict,
    reference_time: datetime | None = None,
    client: ForexFactoryClient | None = None,
) -> AlertPreviewResponse:
    settings = get_settings()
    alert_policy = policy if isinstance(policy, AlertPolicy) else AlertPolicy.model_validate(policy)
    generated_at = reference_time or datetime.now(tz=alert_policy.timezone_info)
    source_client = client or ForexFactoryClient.from_settings(settings)
    events = source_client.fetch_calendar_events(reference_time=generated_at)
    if alert_policy.breaking_enabled:
        events.extend(source_client.fetch_breaking_news_events(reference_time=generated_at))
    return preview_alerts(events=events, policy=alert_policy, generated_at=generated_at)


def fetch_source_events(
    policy: AlertPolicy | dict,
    reference_time: datetime | None = None,
    client: ForexFactoryClient | None = None,
) -> list[ForexEvent]:
    settings = get_settings()
    alert_policy = policy if isinstance(policy, AlertPolicy) else AlertPolicy.model_validate(policy)
    generated_at = reference_time or datetime.now(tz=alert_policy.timezone_info)
    source_client = client or ForexFactoryClient.from_settings(settings)
    events = list(source_client.fetch_calendar_events(reference_time=generated_at))
    if alert_policy.breaking_enabled:
        events.extend(
            _normalize_breaking_event_for_scheduler(event, alert_policy, generated_at)
            for event in source_client.fetch_breaking_news_events(reference_time=generated_at)
        )
    return _deduplicate_events(events)


def sync_relevant_calendar_events(
    policy: AlertPolicy | dict,
    reference_time: datetime | None = None,
    client: ForexFactoryClient | None = None,
    repository: EventRepository | None = None,
) -> tuple[list[StoredEvent], list[EventSchedule]]:
    settings = get_settings()
    alert_policy = policy if isinstance(policy, AlertPolicy) else AlertPolicy.model_validate(policy)
    generated_at = reference_time or datetime.now(tz=alert_policy.timezone_info)
    events = fetch_source_events(policy=alert_policy, reference_time=generated_at, client=client)
    relevant_events = filter_relevant_events(events, alert_policy)
    event_repository = repository or EventRepository(settings.events_state_path)
    event_repository.replace_relevant_events(relevant_events, reference_time=generated_at)
    stored_events = event_repository.list_relevant_events(reference_time=generated_at)
    schedules = build_event_schedules([item.event for item in stored_events], alert_policy)
    return stored_events, schedules


def _normalize_breaking_event_for_scheduler(
    event: ForexEvent,
    policy: AlertPolicy,
    reference_time: datetime,
) -> ForexEvent:
    if event.scheduled_at is not None:
        return event
    published_at = event.published_at or reference_time
    scheduled_at = published_at + policy.lead_delta
    return event.model_copy(update={"scheduled_at": scheduled_at})


def _deduplicate_events(events: list[ForexEvent]) -> list[ForexEvent]:
    deduped: dict[str, ForexEvent] = {}
    for event in events:
        deduped[event.id] = event
    return list(deduped.values())
