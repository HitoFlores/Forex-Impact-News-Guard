from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from forex_news_guard.domain.models import EventSchedule, ImpactLevel


class DeliveryChannel(StrEnum):
    TELEGRAM = "telegram"


class RuntimeProbeName(StrEnum):
    SCRAPING = "scraping"
    TELEGRAM = "telegram"
    PRECHECK = "precheck"


class RuntimeProbeStatus(StrEnum):
    IDLE = "idle"
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


class AlertExecutionKind(StrEnum):
    DAILY_SUMMARY = "daily_summary"
    PRECHECK = "precheck"
    ALERT = "alert"
    RESULT = "result"


class AlertDispatchRecord(BaseModel):
    event_id: str
    scheduled_for: datetime
    kind: AlertExecutionKind
    attempt: int = 1
    sent_at: datetime
    channel: DeliveryChannel


class RuntimeProbeState(BaseModel):
    status: RuntimeProbeStatus = RuntimeProbeStatus.IDLE
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error_message: str | None = None
    consecutive_failures: int = 0


class RuntimeObservability(BaseModel):
    scraping: RuntimeProbeState = Field(default_factory=RuntimeProbeState)
    telegram: RuntimeProbeState = Field(default_factory=RuntimeProbeState)
    precheck: RuntimeProbeState = Field(default_factory=RuntimeProbeState)


class RuntimeSyncResult(BaseModel):
    synced_at: datetime
    schedules: list[EventSchedule] = Field(default_factory=list)
    dispatched: list[AlertDispatchRecord] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)


class NotificationMessage(BaseModel):
    title: str
    body: str
    event_id: str
    impact: ImpactLevel
    parse_mode: str = "HTML"
