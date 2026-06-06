from forex_news_guard.core.config import get_settings
from forex_news_guard.domain.models import AlertPolicy
from forex_news_guard.storage.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self, repository: SettingsRepository | None = None) -> None:
        settings = get_settings()
        self.repository = repository or SettingsRepository(settings.settings_state_path)

    def get_policy(self) -> AlertPolicy:
        return self.repository.get_policy()

    def update_policy(self, payload: AlertPolicy | dict) -> AlertPolicy:
        policy = payload if isinstance(payload, AlertPolicy) else AlertPolicy.model_validate(payload)
        return self.repository.save_policy(policy)
