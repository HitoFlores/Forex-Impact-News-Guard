from datetime import datetime

from forex_news_guard.core.config import get_settings
from forex_news_guard.domain.models import AlertPolicy, AlertPreviewResponse, EventSchedule, StoredEvent
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


def sync_relevant_calendar_events(
    policy: AlertPolicy | dict,
    reference_time: datetime | None = None,
    client: ForexFactoryClient | None = None,
    repository: EventRepository | None = None,
) -> tuple[list[StoredEvent], list[EventSchedule]]:
    settings = get_settings()
    alert_policy = policy if isinstance(policy, AlertPolicy) else AlertPolicy.model_validate(policy)
    generated_at = reference_time or datetime.now(tz=alert_policy.timezone_info)
    source_client = client or ForexFactoryClient.from_settings(settings)
    events = source_client.fetch_calendar_events(reference_time=generated_at)
    relevant_events = filter_relevant_events(events, alert_policy)
    event_repository = repository or EventRepository(settings.events_db_path)
    event_repository.replace_relevant_events(relevant_events, reference_time=generated_at)
    stored_events = event_repository.list_relevant_events(reference_time=generated_at)
    schedules = build_event_schedules([item.event for item in stored_events], alert_policy)
    return stored_events, schedules
