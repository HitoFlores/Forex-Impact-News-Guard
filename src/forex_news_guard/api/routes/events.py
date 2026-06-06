from datetime import datetime

from fastapi import APIRouter

from forex_news_guard.core.config import get_settings
from forex_news_guard.domain.models import EventSchedule, StoredEvent
from forex_news_guard.services.event_scheduler import build_event_schedules
from forex_news_guard.services.settings_service import SettingsService
from forex_news_guard.storage.event_repository import EventRepository

router = APIRouter()


@router.get("/relevant", response_model=list[StoredEvent])
def get_relevant_events() -> list[StoredEvent]:
    settings = get_settings()
    repository = EventRepository(settings.events_state_path)
    policy = SettingsService().get_policy()
    now = datetime.now(tz=policy.timezone_info)
    return repository.list_relevant_events(reference_time=now)


@router.get("/schedules/upcoming", response_model=list[EventSchedule])
def get_upcoming_schedules() -> list[EventSchedule]:
    settings = get_settings()
    repository = EventRepository(settings.events_state_path)
    policy = SettingsService().get_policy()
    now = datetime.now(tz=policy.timezone_info)
    events = [item.event for item in repository.list_relevant_events(reference_time=now)]
    return build_event_schedules(events, policy)
