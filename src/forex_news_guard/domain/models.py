from datetime import datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, computed_field


class ImpactLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertKind(StrEnum):
    CALENDAR = "calendar"
    BREAKING = "breaking"


class ForexEvent(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    currency: str = Field(min_length=1, max_length=10)
    impact: ImpactLevel
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    actual: str | None = None
    forecast: str | None = None
    previous: str | None = None
    actual_better_worse: int | None = None
    url: str | None = None
    source: str = "forex_factory"
    is_breaking: bool = False


class AlertPolicy(BaseModel):
    calendar_enabled: bool = True
    breaking_enabled: bool = True
    high_impact_only: bool = True
    allowed_impacts: list[ImpactLevel] | None = None
    currencies: list[str] = Field(default_factory=list)
    lead_minutes: int = Field(default=15, ge=0, le=240)
    revalidate_minutes_before_alert: int = Field(default=2, ge=0, le=60)
    result_check_delay_minutes: int = Field(default=1, ge=0, le=60)
    result_retry_minutes: list[int] = Field(default_factory=lambda: [3, 5])
    include_results: bool = True
    daily_summary_enabled: bool = True
    risk_window_before_minutes: int = Field(default=15, ge=0, le=240)
    risk_window_after_minutes: int = Field(default=15, ge=0, le=240)
    timezone: str = "America/Chihuahua"

    @computed_field
    @property
    def timezone_info(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def risk_before_delta(self) -> timedelta:
        return timedelta(minutes=self.risk_window_before_minutes)

    @property
    def risk_after_delta(self) -> timedelta:
        return timedelta(minutes=self.risk_window_after_minutes)

    @property
    def lead_delta(self) -> timedelta:
        return timedelta(minutes=self.lead_minutes)

    @property
    def revalidate_delta(self) -> timedelta:
        return timedelta(minutes=self.revalidate_minutes_before_alert)

    @property
    def result_check_delta(self) -> timedelta:
        return timedelta(minutes=self.result_check_delay_minutes)

    @property
    def normalized_currencies(self) -> set[str]:
        return {currency.upper() for currency in self.currencies if currency.strip()}

    @property
    def effective_impacts(self) -> set[ImpactLevel]:
        if self.allowed_impacts:
            return set(self.allowed_impacts)
        if self.high_impact_only:
            return {ImpactLevel.HIGH}
        return {ImpactLevel.LOW, ImpactLevel.MEDIUM, ImpactLevel.HIGH}


class PlannedAlert(BaseModel):
    event_id: str
    title: str
    currency: str
    impact: ImpactLevel
    alert_kind: AlertKind
    alert_at: datetime
    reason: str
    source: str
    event_url: str | None = None


class RiskWindow(BaseModel):
    event_id: str
    starts_at: datetime
    ends_at: datetime


class AlertPreviewRequest(BaseModel):
    policy: AlertPolicy = Field(default_factory=AlertPolicy)
    events: list[ForexEvent] = Field(default_factory=list)
    generated_at: datetime | None = None


class AlertPreviewResponse(BaseModel):
    generated_at: datetime
    planned_alerts: list[PlannedAlert]
    risk_windows: list[RiskWindow]


class TelegramSmokeTestResponse(BaseModel):
    sent_messages: list[str]


class StoredEvent(BaseModel):
    event: ForexEvent
    stored_at: datetime
    event_date: str


class ScheduledEventCheckKind(StrEnum):
    PRECHECK = "precheck"
    ALERT = "alert"
    RESULT = "result"


class ScheduledEventCheck(BaseModel):
    event_id: str
    kind: ScheduledEventCheckKind
    scheduled_for: datetime
    attempt: int = 1


class EventSchedule(BaseModel):
    event: ForexEvent
    precheck: ScheduledEventCheck
    alert: ScheduledEventCheck
    result_checks: list[ScheduledEventCheck] = Field(default_factory=list)
