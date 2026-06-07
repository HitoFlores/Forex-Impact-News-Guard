from __future__ import annotations

from forex_news_guard.domain.models import AlertPolicy
from forex_news_guard.storage.json_state_store import JsonStateStore


class SettingsRepository:
    def __init__(self, state_path: str) -> None:
        self.store = JsonStateStore(state_path)

    def get_policy(self) -> AlertPolicy:
        payload = self.store.load(default={})
        if not payload:
            policy = AlertPolicy()
            self.save_policy(policy)
            return policy
        return AlertPolicy.model_validate(payload)

    def save_policy(self, policy: AlertPolicy) -> AlertPolicy:
        self.store.save(policy.model_dump(mode="json"))
        return policy
