from datetime import datetime

from forex_news_guard.domain.models import (
    AlertKind,
    AlertPolicy,
    AlertPreviewResponse,
    ForexEvent,
    ImpactLevel,
    PlannedAlert,
    RiskWindow,
)


def preview_alerts(
    events: list[ForexEvent],
    policy: AlertPolicy,
    generated_at: datetime,
) -> AlertPreviewResponse:
    planned_alerts: list[PlannedAlert] = []
    risk_windows: list[RiskWindow] = []

    for event in events:
        if policy.high_impact_only and event.impact != ImpactLevel.HIGH:
            continue

        if policy.calendar_enabled and event.scheduled_at is not None:
            risk_windows.append(
                RiskWindow(
                    event_id=event.id,
                    starts_at=event.scheduled_at - policy.risk_before_delta,
                    ends_at=event.scheduled_at + policy.risk_after_delta,
                )
            )
            planned_alerts.append(
                PlannedAlert(
                    event_id=event.id,
                    title=event.title,
                    currency=event.currency,
                    impact=event.impact,
                    alert_kind=AlertKind.CALENDAR,
                    alert_at=event.scheduled_at - policy.lead_delta,
                    reason=f"Alerta {policy.lead_minutes} minutos antes del evento programado.",
                    source=event.source,
                    event_url=event.url,
                )
            )

        if policy.breaking_enabled and event.is_breaking:
            alert_at = event.published_at or generated_at
            planned_alerts.append(
                PlannedAlert(
                    event_id=event.id,
                    title=event.title,
                    currency=event.currency,
                    impact=event.impact,
                    alert_kind=AlertKind.BREAKING,
                    alert_at=alert_at,
                    reason="Breaking news de alto impacto detectada y enviada de inmediato.",
                    source=event.source,
                    event_url=event.url,
                )
            )

    planned_alerts.sort(key=lambda item: item.alert_at)
    risk_windows.sort(key=lambda item: item.starts_at)
    return AlertPreviewResponse(
        generated_at=generated_at,
        planned_alerts=planned_alerts,
        risk_windows=risk_windows,
    )
