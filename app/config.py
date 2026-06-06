from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения из переменных окружения / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""
    admin_telegram_ids: Annotated[list[int], NoDecode] = []

    database_url: str = "sqlite+aiosqlite:///./vpnbot.sqlite3"

    payment_amount_rub: int = 175
    payment_period_days: int = 30
    trial_period_days: int = 2
    payment_details_text: str = (
        "Реквизиты для перевода: укажите здесь номер карты или СБП."
    )
    support_contact: str = "@support"

    xui_request_timeout: int = 15

    # Антишеринг-мониторинг (мягкий, без автоблокировки в MVP)
    anti_sharing_enabled: bool = True
    device_policy: str = "soft"
    default_ip_limit: int = 3
    warn_threshold_24h: int = 5
    critical_threshold_24h: int = 8
    auto_block_enabled: bool = False
    tracking_window_hours: int = 24
    anti_sharing_poll_minutes: int = 5

    @field_validator("bot_token", mode="before")
    @classmethod
    def _clean_bot_token(cls, value: object) -> object:
        """Убирает пробелы и обрамляющие кавычки вокруг токена."""
        if isinstance(value, str):
            cleaned = value.strip().strip('"').strip("'").strip()
            return cleaned
        return value

    @field_validator("admin_telegram_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        """Разрешает задавать ADMIN_TELEGRAM_IDS как строку '1,2,3' или одно число."""
        if value is None or value == "":
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        return value

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
