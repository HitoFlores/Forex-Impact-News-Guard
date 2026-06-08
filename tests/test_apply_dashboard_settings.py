from pathlib import Path
from uuid import uuid4

from scripts import apply_dashboard_settings


def _sandbox_tmp_dir() -> Path:
    path = Path(__file__).resolve().parents[1] / ".tmp" / f"forex-guard-test-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_build_policy_from_env_parses_dashboard_inputs(monkeypatch) -> None:
    tmp_path = _sandbox_tmp_dir()
    monkeypatch.setattr(apply_dashboard_settings, "STATE_DIR", tmp_path)
    monkeypatch.setattr(apply_dashboard_settings, "SETTINGS_PATH", tmp_path / "settings.json")

    monkeypatch.setenv("INPUT_CALENDAR_ENABLED", "true")
    monkeypatch.setenv("INPUT_BREAKING_ENABLED", "false")
    monkeypatch.setenv("INPUT_HIGH_IMPACT_ONLY", "false")
    monkeypatch.setenv("INPUT_CURRENCIES", "usd, eur , jpy")
    monkeypatch.setenv("INPUT_LEAD_MINUTES", "25")
    monkeypatch.setenv("INPUT_REVALIDATE_MINUTES_BEFORE_ALERT", "4")
    monkeypatch.setenv("INPUT_RESULT_CHECK_DELAY_MINUTES", "2")
    monkeypatch.setenv("INPUT_INCLUDE_RESULTS", "true")
    monkeypatch.setenv("INPUT_DAILY_SUMMARY_ENABLED", "false")
    monkeypatch.setenv("INPUT_RISK_WINDOW_BEFORE_MINUTES", "30")
    monkeypatch.setenv("INPUT_RISK_WINDOW_AFTER_MINUTES", "45")
    monkeypatch.setenv("INPUT_TIMEZONE", "America/Chihuahua")
    monkeypatch.setenv("INPUT_ALLOWED_IMPACTS", "medium,high")

    policy = apply_dashboard_settings.build_policy_from_env()

    assert policy.calendar_enabled is True
    assert policy.breaking_enabled is False
    assert policy.high_impact_only is False
    assert policy.currencies == ["USD", "EUR", "JPY"]
    assert policy.lead_minutes == 25
    assert policy.revalidate_minutes_before_alert == 4
    assert policy.result_check_delay_minutes == 2
    assert policy.include_results is True
    assert policy.daily_summary_enabled is False
    assert policy.risk_window_before_minutes == 30
    assert policy.risk_window_after_minutes == 45
    assert [impact.value for impact in policy.allowed_impacts or []] == ["medium", "high"]


def test_build_policy_from_env_defaults_to_all_impacts_when_not_high_only(
    monkeypatch
) -> None:
    tmp_path = _sandbox_tmp_dir()
    monkeypatch.setattr(apply_dashboard_settings, "STATE_DIR", tmp_path)
    monkeypatch.setattr(apply_dashboard_settings, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setenv("INPUT_HIGH_IMPACT_ONLY", "false")
    monkeypatch.delenv("INPUT_ALLOWED_IMPACTS", raising=False)

    policy = apply_dashboard_settings.build_policy_from_env()

    assert [impact.value for impact in policy.allowed_impacts or []] == ["low", "medium", "high"]
