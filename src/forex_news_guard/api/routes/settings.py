from fastapi import APIRouter

from forex_news_guard.domain.models import AlertPolicy
from forex_news_guard.services.settings_service import SettingsService

router = APIRouter()


@router.get("", response_model=AlertPolicy)
def get_settings() -> AlertPolicy:
    return SettingsService().get_policy()


@router.put("", response_model=AlertPolicy)
def update_settings(payload: AlertPolicy) -> AlertPolicy:
    return SettingsService().update_policy(payload)
