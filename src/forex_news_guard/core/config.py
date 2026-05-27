from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Forex Impact News Guard"
    app_version: str = "0.1.0"
    default_timezone: str = "America/Chihuahua"
    forex_factory_base_url: str = "https://www.forexfactory.com"
    forex_factory_calendar_url: str = "https://www.forexfactory.com/calendar"
    forex_factory_news_url: str = "https://www.forexfactory.com/news?sc_lang=en"
    forex_factory_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    forex_factory_cookie: str | None = None
    forex_factory_timeout_seconds: float = 20.0
    state_dir: str = str(Path(".state").resolve())
    events_db_path: str = str(Path(".state/forex_news_guard.db").resolve())
    scheduler_sync_interval_minutes: int = 30
    scheduler_tick_seconds: int = 30
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="FOREX_GUARD_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
