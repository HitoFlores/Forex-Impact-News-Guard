from datetime import datetime

from fastapi import APIRouter, HTTPException

from forex_news_guard.domain.models import AlertPolicy, AlertPreviewRequest, AlertPreviewResponse
from forex_news_guard.integrations.forex_factory import ForexFactoryBlockedError, ForexFactoryError
from forex_news_guard.services.alert_planner import preview_alerts
from forex_news_guard.services.forex_factory_monitor import preview_live_alerts

router = APIRouter()


@router.post("/preview", response_model=AlertPreviewResponse)
def preview_alerts_route(payload: AlertPreviewRequest) -> AlertPreviewResponse:
    generated_at = payload.generated_at or datetime.now(tz=payload.policy.timezone_info)
    return preview_alerts(events=payload.events, policy=payload.policy, generated_at=generated_at)


@router.post("/forex-factory/live-preview", response_model=AlertPreviewResponse)
def preview_forex_factory_live_alerts(payload: AlertPolicy | None = None) -> AlertPreviewResponse:
    policy = payload or AlertPolicy()
    try:
        return preview_live_alerts(policy=policy)
    except ForexFactoryBlockedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ForexFactoryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
