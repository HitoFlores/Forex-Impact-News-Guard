from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from forex_news_guard.core.config import get_settings
from forex_news_guard.domain.models import AlertPolicy, EventSchedule, ForexEvent, ScheduledEventCheck, StoredEvent
from forex_news_guard.domain.runtime import (
    AlertDispatchRecord,
    AlertExecutionKind,
    DeliveryChannel,
    RuntimeProbeName,
    RuntimeSyncResult,
)
from forex_news_guard.integrations.forex_factory import ForexFactoryClient
from forex_news_guard.services.event_scheduler import build_event_schedules, filter_relevant_events
from forex_news_guard.services.forex_factory_monitor import sync_relevant_calendar_events
from forex_news_guard.services.notification_formatter import (
    build_daily_summary_message,
    build_grouped_pre_alert_message,
    build_grouped_result_message,
    build_pre_alert_message,
    build_result_message,
)
from forex_news_guard.services.settings_service import SettingsService
from forex_news_guard.services.telegram_notifier import TelegramNotifier
from forex_news_guard.storage.event_repository import EventRepository
from forex_news_guard.storage.runtime_repository import RuntimeRepository

logger = logging.getLogger(__name__)


class RuntimeSchedulerService:
    def __init__(
        self,
        policy: AlertPolicy | None = None,
        client: ForexFactoryClient | None = None,
        event_repository: EventRepository | None = None,
        runtime_repository: RuntimeRepository | None = None,
        notifier: TelegramNotifier | None = None,
        settings_service: SettingsService | None = None,
    ) -> None:
        settings = get_settings()
        self.settings_service = settings_service or SettingsService()
        self.policy = policy or self.settings_service.get_policy()
        self.client = client or ForexFactoryClient.from_settings(settings)
        self.event_repository = event_repository or EventRepository(settings.events_state_path)
        self.runtime_repository = runtime_repository or RuntimeRepository(settings.runtime_state_path)
        self.notifier = notifier or self._build_notifier()
        self.scheduler = BackgroundScheduler(timezone=self.policy.timezone)

    def start(self) -> None:
        settings = get_settings()
        self.scheduler.add_job(
            self.run_cycle,
            "interval",
            minutes=settings.scheduler_sync_interval_minutes,
            id="sync-relevant-events",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.dispatch_due_checks,
            "interval",
            seconds=settings.scheduler_tick_seconds,
            id="dispatch-due-checks",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)

    def run_once(self) -> RuntimeSyncResult:
        self._reload_policy()
        reference_time = datetime.now(tz=self.policy.timezone_info)
        return self.run_cycle_at(reference_time)

    def run_full_cycle(self) -> tuple[RuntimeSyncResult, RuntimeSyncResult]:
        self._reload_policy()
        reference_time = datetime.now(tz=self.policy.timezone_info)
        sync_result = self.run_cycle_at(reference_time)
        dispatch_result = self.dispatch_due_checks_at(reference_time)
        logger.info(
            "Full worker cycle finished at=%s synced_events=%s due_dispatches=%s skipped=%s",
            reference_time.isoformat(),
            len(sync_result.schedules),
            len(dispatch_result.dispatched),
            len(dispatch_result.skipped),
        )
        return sync_result, dispatch_result

    def run_cycle(self) -> RuntimeSyncResult:
        return self.run_once()

    def run_cycle_at(self, reference_time: datetime) -> RuntimeSyncResult:
        try:
            stored_events, schedules = sync_relevant_calendar_events(
                policy=self.policy,
                reference_time=reference_time,
                client=self.client,
                repository=self.event_repository,
            )
        except Exception as error:
            self.runtime_repository.record_probe_error(
                RuntimeProbeName.SCRAPING,
                attempted_at=reference_time,
                error_message=f"{type(error).__name__}: {error}",
            )
            raise
        self.runtime_repository.record_probe_success(
            RuntimeProbeName.SCRAPING,
            attempted_at=reference_time,
        )
        dispatched: list[AlertDispatchRecord] = []
        self._send_daily_summary_if_needed([item.event for item in stored_events], reference_time, dispatched)
        logger.info(
            "Synchronized relevant_events=%s schedules=%s daily_dispatches=%s at=%s",
            len(stored_events),
            len(schedules),
            len(dispatched),
            reference_time.isoformat(),
        )
        return RuntimeSyncResult(synced_at=reference_time, schedules=schedules, dispatched=dispatched)

    def dispatch_due_checks(self) -> RuntimeSyncResult:
        self._reload_policy()
        reference_time = datetime.now(tz=self.policy.timezone_info)
        return self.dispatch_due_checks_at(reference_time)

    def dispatch_due_checks_at(self, reference_time: datetime) -> RuntimeSyncResult:
        stored_events = self.event_repository.list_relevant_events(reference_time=reference_time)
        schedules = build_event_schedules([item.event for item in stored_events], self.policy)
        dispatched: list[AlertDispatchRecord] = []
        skipped: list[str] = []
        stored_events, schedules, blocked_alert_event_ids = self._revalidate_due_prechecks(
            stored_events=stored_events,
            schedules=schedules,
            reference_time=reference_time,
            dispatched=dispatched,
            skipped=skipped,
        )
        event_map = {stored.event.id: stored.event for stored in stored_events}
        self._dispatch_grouped_alerts(
            schedules,
            event_map,
            reference_time,
            dispatched,
            skipped,
            blocked_alert_event_ids,
        )
        self._dispatch_grouped_results(schedules, event_map, reference_time, dispatched, skipped)
        logger.info(
            "Processed due checks schedules=%s dispatched=%s skipped=%s at=%s",
            len(schedules),
            len(dispatched),
            len(skipped),
            reference_time.isoformat(),
        )

        return RuntimeSyncResult(
            synced_at=reference_time,
            schedules=schedules,
            dispatched=dispatched,
            skipped=skipped,
        )

    def _revalidate_due_prechecks(
        self,
        stored_events: list[StoredEvent],
        schedules: list[EventSchedule],
        reference_time: datetime,
        dispatched: list[AlertDispatchRecord],
        skipped: list[str],
    ) -> tuple[list[StoredEvent], list[EventSchedule], set[str]]:
        pending_prechecks = [
            schedule
            for schedule in schedules
            if schedule.precheck.scheduled_for <= reference_time
            and not self.runtime_repository.has_been_dispatched(
                event_id=schedule.event.id,
                kind=AlertExecutionKind.PRECHECK,
                scheduled_for=schedule.precheck.scheduled_for,
                attempt=schedule.precheck.attempt,
            )
        ]
        if not pending_prechecks:
            return stored_events, schedules, set()

        refreshed_stored_events = stored_events
        refreshed_schedules = schedules
        try:
            refreshed_events = self.client.fetch_calendar_events(reference_time=reference_time)
            relevant_events = filter_relevant_events(refreshed_events, self.policy)
            self.event_repository.replace_relevant_events(relevant_events, reference_time=reference_time)
            refreshed_stored_events = self.event_repository.list_relevant_events(reference_time=reference_time)
            refreshed_schedules = build_event_schedules([item.event for item in refreshed_stored_events], self.policy)
            self.runtime_repository.record_probe_success(
                RuntimeProbeName.SCRAPING,
                attempted_at=reference_time,
            )
            self.runtime_repository.record_probe_success(
                RuntimeProbeName.PRECHECK,
                attempted_at=reference_time,
            )
            logger.info("Revalidated %s events for %s due prechecks", len(relevant_events), len(pending_prechecks))
        except Exception as error:
            self.runtime_repository.record_probe_error(
                RuntimeProbeName.SCRAPING,
                attempted_at=reference_time,
                error_message=f"{type(error).__name__}: {error}",
            )
            self.runtime_repository.record_probe_error(
                RuntimeProbeName.PRECHECK,
                attempted_at=reference_time,
                error_message=f"{type(error).__name__}: {error}",
            )
            logger.exception("Failed to revalidate calendar events before alert dispatch")
            skipped.append(f"precheck-refresh-failed:{len(pending_prechecks)}")
            return stored_events, schedules, {schedule.event.id for schedule in pending_prechecks}

        completed_prechecks = [
            schedule
            for schedule in refreshed_schedules
            if schedule.precheck.scheduled_for <= reference_time
            and not self.runtime_repository.has_been_dispatched(
                event_id=schedule.event.id,
                kind=AlertExecutionKind.PRECHECK,
                scheduled_for=schedule.precheck.scheduled_for,
                attempt=schedule.precheck.attempt,
            )
        ]
        for schedule in completed_prechecks:
            record = AlertDispatchRecord(
                event_id=schedule.event.id,
                kind=AlertExecutionKind.PRECHECK,
                attempt=schedule.precheck.attempt,
                scheduled_for=schedule.precheck.scheduled_for,
                sent_at=reference_time,
                channel=DeliveryChannel.TELEGRAM,
            )
            self.runtime_repository.record_dispatch(record)
            dispatched.append(record)

        return refreshed_stored_events, refreshed_schedules, set()

    def _dispatch_grouped_alerts(
        self,
        schedules: list[EventSchedule],
        event_map: dict[str, ForexEvent],
        reference_time: datetime,
        dispatched: list[AlertDispatchRecord],
        skipped: list[str],
        blocked_alert_event_ids: set[str],
    ) -> None:
        grouped: dict[datetime, list[EventSchedule]] = {}
        for schedule in schedules:
            grouped.setdefault(schedule.alert.scheduled_for, []).append(schedule)

        for scheduled_for, group in grouped.items():
            due_group = [item for item in group if item.alert.scheduled_for <= reference_time]
            if not due_group:
                continue
            blocked_group = [item for item in due_group if item.event.id in blocked_alert_event_ids]
            for item in blocked_group:
                skipped.append(f"{item.event.id}:alert-blocked-precheck")
            due_group = [item for item in due_group if item.event.id not in blocked_alert_event_ids]
            if not due_group:
                continue
            events = [event_map.get(item.event.id, item.event) for item in due_group]
            pending = [
                item
                for item in due_group
                if not self.runtime_repository.has_been_dispatched(
                    event_id=item.event.id,
                    kind=AlertExecutionKind.ALERT,
                    scheduled_for=item.alert.scheduled_for,
                    attempt=item.alert.attempt,
                )
            ]
            if not pending:
                skipped.append(f"group-alert:{scheduled_for.isoformat()}")
                continue

            message = (
                build_pre_alert_message(events[0], self.policy.lead_minutes)
                if len(events) == 1
                else build_grouped_pre_alert_message(events, self.policy.lead_minutes)
            )
            self._send_telegram_message(message, reference_time)
            logger.info(
                "Sent alert group events=%s alert_at=%s ids=%s",
                len(pending),
                scheduled_for.isoformat(),
                ",".join(item.event.id for item in pending),
            )
            for item in pending:
                record = AlertDispatchRecord(
                    event_id=item.event.id,
                    kind=AlertExecutionKind.ALERT,
                    attempt=item.alert.attempt,
                    scheduled_for=item.alert.scheduled_for,
                    sent_at=reference_time,
                    channel=DeliveryChannel.TELEGRAM,
                )
                self.runtime_repository.record_dispatch(record)
                dispatched.append(record)

    def _dispatch_grouped_results(
        self,
        schedules: list[EventSchedule],
        event_map: dict[str, ForexEvent],
        reference_time: datetime,
        dispatched: list[AlertDispatchRecord],
        skipped: list[str],
    ) -> None:
        grouped: dict[tuple[datetime, int], list[tuple[EventSchedule, ScheduledEventCheck]]] = {}
        for schedule in schedules:
            for result_check in schedule.result_checks:
                grouped.setdefault((result_check.scheduled_for, result_check.attempt), []).append((schedule, result_check))

        for (scheduled_for, attempt), group in grouped.items():
            due_group = [item for item in group if item[1].scheduled_for <= reference_time]
            if not due_group or not self.policy.include_results:
                continue

            pending = [
                item
                for item in due_group
                if not self.runtime_repository.has_been_dispatched(
                    event_id=item[0].event.id,
                    kind=AlertExecutionKind.RESULT,
                    scheduled_for=item[1].scheduled_for,
                    attempt=item[1].attempt,
                )
            ]
            if not pending:
                skipped.append(f"group-result:{scheduled_for.isoformat()}:{attempt}")
                continue

            events = [event_map.get(schedule.event.id, schedule.event) for schedule, _ in pending]
            message = (
                build_result_message(events[0], reference_time)
                if len(events) == 1
                else build_grouped_result_message(events, reference_time)
            )
            self._send_telegram_message(message, reference_time)
            logger.info(
                "Sent result group events=%s check_at=%s attempt=%s ids=%s",
                len(pending),
                scheduled_for.isoformat(),
                attempt,
                ",".join(schedule.event.id for schedule, _ in pending),
            )
            for schedule, result_check in pending:
                record = AlertDispatchRecord(
                    event_id=schedule.event.id,
                    kind=AlertExecutionKind.RESULT,
                    attempt=result_check.attempt,
                    scheduled_for=result_check.scheduled_for,
                    sent_at=reference_time,
                    channel=DeliveryChannel.TELEGRAM,
                )
                self.runtime_repository.record_dispatch(record)
                dispatched.append(record)

    def _send_daily_summary_if_needed(
        self,
        events: list[ForexEvent],
        reference_time: datetime,
        dispatched: list[AlertDispatchRecord],
    ) -> None:
        scheduled_for = reference_time.replace(hour=0, minute=0, second=0, microsecond=0)
        if self.runtime_repository.has_been_dispatched(
            event_id=f"daily-summary-{reference_time.date().isoformat()}",
            kind=AlertExecutionKind.DAILY_SUMMARY,
            scheduled_for=scheduled_for,
            attempt=1,
        ):
            return

        if not self.policy.daily_summary_enabled:
            return

        high_impact_events = [event for event in events if event.impact.value == "high"]
        message = build_daily_summary_message(high_impact_events, reference_time)
        self._send_telegram_message(message, reference_time)
        logger.info(
            "Sent daily summary high_impact_events=%s date=%s",
            len(high_impact_events),
            reference_time.date().isoformat(),
        )
        record = AlertDispatchRecord(
            event_id=message.event_id,
            kind=AlertExecutionKind.DAILY_SUMMARY,
            attempt=1,
            scheduled_for=scheduled_for,
            sent_at=reference_time,
            channel=DeliveryChannel.TELEGRAM,
        )
        self.runtime_repository.record_dispatch(record)
        dispatched.append(record)

    def _dispatch_if_due(
        self,
        event: ForexEvent,
        check: ScheduledEventCheck,
        reference_time: datetime,
        dispatched: list[AlertDispatchRecord],
        skipped: list[str],
    ) -> None:
        if check.scheduled_for > reference_time:
            return

        execution_kind = AlertExecutionKind(check.kind.value)
        if self.runtime_repository.has_been_dispatched(
            event_id=event.id,
            kind=execution_kind,
            scheduled_for=check.scheduled_for,
            attempt=check.attempt,
        ):
            skipped.append(f"{event.id}:{check.kind.value}:{check.attempt}")
            return

        if check.kind.value == "alert":
            message = build_pre_alert_message(event, self.policy.lead_minutes)
        elif check.kind.value == "result":
            if not self.policy.include_results:
                skipped.append(f"{event.id}:result-disabled")
                return
            message = build_result_message(event, reference_time)
        else:
            skipped.append(f"{event.id}:precheck-no-notify")
            self.runtime_repository.record_dispatch(
                AlertDispatchRecord(
                    event_id=event.id,
                    kind=execution_kind,
                    attempt=check.attempt,
                    scheduled_for=check.scheduled_for,
                    sent_at=reference_time,
                    channel=DeliveryChannel.TELEGRAM,
                )
            )
            return

        self._send_telegram_message(message, reference_time)
        record = AlertDispatchRecord(
            event_id=event.id,
            kind=execution_kind,
            attempt=check.attempt,
            scheduled_for=check.scheduled_for,
            sent_at=reference_time,
            channel=DeliveryChannel.TELEGRAM,
        )
        self.runtime_repository.record_dispatch(record)
        dispatched.append(record)

    def _build_notifier(self) -> TelegramNotifier:
        settings = get_settings()
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            raise RuntimeError(
                "Configura FOREX_GUARD_TELEGRAM_BOT_TOKEN y FOREX_GUARD_TELEGRAM_CHAT_ID para usar Telegram."
            )
        return TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            timeout_seconds=settings.forex_factory_timeout_seconds,
        )

    def _send_telegram_message(self, message, reference_time: datetime) -> None:  # noqa: ANN001
        try:
            self.notifier.send(message)
        except Exception as error:
            self.runtime_repository.record_probe_error(
                RuntimeProbeName.TELEGRAM,
                attempted_at=reference_time,
                error_message=f"{type(error).__name__}: {error}",
            )
            raise
        self.runtime_repository.record_probe_success(
            RuntimeProbeName.TELEGRAM,
            attempted_at=reference_time,
        )

    def _reload_policy(self) -> None:
        self.policy = self.settings_service.get_policy()
