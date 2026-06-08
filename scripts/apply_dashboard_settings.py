from __future__ import annotations

import json
import os
from pathlib import Path

from forex_news_guard.domain.models import AlertPolicy, ImpactLevel


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".state"
SETTINGS_PATH = STATE_DIR / "settings.json"


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _parse_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def _parse_impacts(value: str | None, high_impact_only: bool) -> list[ImpactLevel] | None:
    if value is None or value.strip() == "":
        return None if high_impact_only else [
            ImpactLevel.LOW,
            ImpactLevel.MEDIUM,
            ImpactLevel.HIGH,
        ]

    values = [item.strip().lower() for item in value.split(",") if item.strip()]
    return [ImpactLevel(item) for item in values]


def load_existing_policy() -> AlertPolicy:
    if not SETTINGS_PATH.exists():
        return AlertPolicy()
    return AlertPolicy.model_validate(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))


def build_policy_from_env() -> AlertPolicy:
    current = load_existing_policy()
    high_impact_only = _parse_bool(
        os.getenv("INPUT_HIGH_IMPACT_ONLY"),
        current.high_impact_only,
    )
    payload = {
        "calendar_enabled": _parse_bool(os.getenv("INPUT_CALENDAR_ENABLED"), current.calendar_enabled),
        "breaking_enabled": _parse_bool(os.getenv("INPUT_BREAKING_ENABLED"), current.breaking_enabled),
        "high_impact_only": high_impact_only,
        "currencies": _parse_csv(os.getenv("INPUT_CURRENCIES")),
        "lead_minutes": _parse_int(os.getenv("INPUT_LEAD_MINUTES"), current.lead_minutes),
        "revalidate_minutes_before_alert": _parse_int(
            os.getenv("INPUT_REVALIDATE_MINUTES_BEFORE_ALERT"),
            current.revalidate_minutes_before_alert,
        ),
        "result_check_delay_minutes": _parse_int(
            os.getenv("INPUT_RESULT_CHECK_DELAY_MINUTES"),
            current.result_check_delay_minutes,
        ),
        "result_retry_minutes": current.result_retry_minutes,
        "include_results": _parse_bool(os.getenv("INPUT_INCLUDE_RESULTS"), current.include_results),
        "daily_summary_enabled": _parse_bool(
            os.getenv("INPUT_DAILY_SUMMARY_ENABLED"),
            current.daily_summary_enabled,
        ),
        "risk_window_before_minutes": _parse_int(
            os.getenv("INPUT_RISK_WINDOW_BEFORE_MINUTES"),
            current.risk_window_before_minutes,
        ),
        "risk_window_after_minutes": _parse_int(
            os.getenv("INPUT_RISK_WINDOW_AFTER_MINUTES"),
            current.risk_window_after_minutes,
        ),
        "timezone": os.getenv("INPUT_TIMEZONE") or current.timezone,
        "allowed_impacts": _parse_impacts(os.getenv("INPUT_ALLOWED_IMPACTS"), high_impact_only),
    }
    return AlertPolicy.model_validate(payload)


def main() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    policy = build_policy_from_env()
    SETTINGS_PATH.write_text(
        json.dumps(policy.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
