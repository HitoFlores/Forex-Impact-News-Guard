from pathlib import Path

from forex_news_guard.domain.models import AlertPolicy, ImpactLevel
from forex_news_guard.services.settings_service import SettingsService
from forex_news_guard.storage.settings_repository import SettingsRepository


def test_settings_service_persists_policy(tmp_path: Path) -> None:
    repository = SettingsRepository(str(tmp_path / "settings.db"))
    service = SettingsService(repository=repository)

    updated = service.update_policy(
        AlertPolicy(
            allowed_impacts=[ImpactLevel.HIGH, ImpactLevel.MEDIUM],
            currencies=["USD", "EUR"],
            lead_minutes=7,
            daily_summary_enabled=False,
        )
    )
    loaded = service.get_policy()

    assert updated.lead_minutes == 7
    assert loaded.allowed_impacts == [ImpactLevel.HIGH, ImpactLevel.MEDIUM]
    assert loaded.currencies == ["USD", "EUR"]
    assert loaded.daily_summary_enabled is False
