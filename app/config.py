from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения из переменных окружения / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""
    admin_telegram_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    database_url: str = "sqlite+aiosqlite:///./vpnbot.sqlite3"

    # Ключ для шифрования секретов в БД (пароли панелей). Произвольная строка;
    # из неё выводится ключ Fernet. Пусто — секреты хранятся в открытом виде
    # (только для разработки). В проде задайте стойкое случайное значение.
    secret_key: str = ""

    payment_amount_rub: int = Field(default=175, ge=1)
    payment_period_days: int = Field(default=30, ge=1, le=3660)
    trial_period_days: int = Field(default=3, ge=1, le=365)
    payment_details_text: str = (
        "<code>+70000000000</code> (банк по СБП)\n"
        "<code>0000 0000 0000 0000</code> (банк на карту)"
    )
    support_contact: str = "@support"

    xui_request_timeout: int = Field(default=15, ge=1, le=120)

    # Уровень логирования приложения: DEBUG/INFO/WARNING/ERROR
    log_level: str = "INFO"
    # Подробный лог HTTP-запросов к 3x-ui (метод/путь/статус). DEBUG-уровень.
    xui_debug: bool = False

    # Антишеринг-мониторинг (мягкий, без автоблокировки в MVP)
    anti_sharing_enabled: bool = True
    device_policy: str = "soft"
    default_ip_limit: int = Field(default=3, ge=0)
    warn_threshold_24h: int = Field(default=5, ge=1)
    critical_threshold_24h: int = Field(default=8, ge=1)
    auto_block_enabled: bool = False
    tracking_window_hours: int = Field(default=24, ge=1)
    anti_sharing_poll_minutes: int = Field(default=5, ge=0)

    # Период фоновой проверки доступности серверов, секунды (0 — отключить).
    server_health_poll_seconds: int = Field(default=60, ge=0)

    # Период проверки истекающих подписок для уведомлений, секунды (0 — отключить).
    expiry_notify_poll_seconds: int = Field(default=300, ge=0)

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

    @field_validator("log_level", mode="before")
    @classmethod
    def _clean_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip().upper()
            allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if cleaned in allowed:
                return cleaned
        return value

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_telegram_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
