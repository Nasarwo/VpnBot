"""Миграция ``trial_grants`` переносит существующие факты использования trial.

SQLite проверяется всегда; PostgreSQL — при ``VPNBOT_TEST_PG_URL`` (отдельная
тестовая база: схема ``public`` пересоздаётся).
"""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.db.models import User
from app.services import billing
from tests.test_whitelist_pg import PG_URL

ROOT = Path(__file__).resolve().parents[1]
BEFORE = "a4b5c6d7e8f9"
T0 = datetime(2026, 9, 1, 12, 0)


def _alembic(monkeypatch, url: str) -> Config:
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    assert get_settings().database_url == url  # env.py мигрирует именно её
    # Без ini-файла env.py не вызывает fileConfig, который отключил бы логгеры
    # (и caplog) в последующих тестах.
    config = Config()
    config.set_main_option("script_location", str(ROOT / "app/migrations"))
    return config


async def _execute(url: str, *statements: tuple[str, dict]) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            for sql, params in statements:
                await conn.execute(text(sql), params)
    finally:
        await engine.dispose()


async def _fetch(url: str, sql: str) -> list[tuple]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            return [tuple(row) for row in await conn.execute(text(sql))]
    finally:
        await engine.dispose()


def _user(user_id, telegram_id, trial_used):
    return (
        "INSERT INTO users (id, telegram_id, role, trial_used, onboarding_done) "
        "VALUES (:id, :tg, 'USER', :trial, false)",
        {"id": user_id, "tg": telegram_id, "trial": trial_used},
    )


def _audit(action, actor, entity_id, payload, minutes):
    return (
        "INSERT INTO audit_logs (actor_user_id, action, entity_type, entity_id, payload,"
        " created_at) VALUES (:actor, :action, :type, :entity, :payload, :at)",
        {
            "actor": actor,
            "action": action,
            "type": "user" if action.startswith("user.") else "vpn_client",
            "entity": entity_id,
            "payload": json.dumps(payload),
            "at": T0 + timedelta(minutes=minutes),
        },
    )


def _reset_audit(user_id, telegram_id, minutes, action="user.self_reset"):
    return _audit(action, user_id, user_id, {"telegram_id": telegram_id}, minutes)


def _trial_audit(user_id, minutes):
    return _audit("billing.trial_granted", user_id, 900 + minutes, {"period_days": 3}, minutes)


def _seed_sqlite() -> list[tuple[str, dict]]:
    """SQLite без PRAGMA foreign_keys: actor_user_id удалённых пользователей сохранён."""
    return [
        _user(1, 100, True),   # trial у текущего пользователя
        _user(2, 200, False),  # trial не брал
        _user(3, None, True),  # аккаунт только сайта: Telegram ID неизвестен
        # Пользователь 5 (tg 500) получил trial и сбросил бота — User удалён.
        _trial_audit(5, 10),
        _reset_audit(5, 500, 20),
        # id 1 повторно выдан SQLite: прежний владелец (tg 300) взял trial и
        # сбросился (административным сбросом), затем id 1 получил tg 100.
        _trial_audit(1, 1),
        _reset_audit(1, 300, 2, action="user.reset_bot_state"),
        _trial_audit(1, 30),
        # Сброс без trial (tg 600) факта не создаёт.
        _reset_audit(6, 600, 40),
    ]


def _seed_postgres() -> list[tuple[str, dict]]:
    """PostgreSQL: удаление пользователя обнуляет actor_user_id (ON DELETE SET NULL)."""
    statements = [
        _user(1, 100, True),
        _user(2, 200, False),
        _user(5, 500, True),
        _trial_audit(1, 1),
        _trial_audit(5, 10),
        _reset_audit(5, 500, 20),
        ("DELETE FROM users WHERE id = 5", {}),
    ]
    # timestamptz: явный UTC, независимо от часового пояса сервера.
    return [
        (sql, {k: v.replace(tzinfo=UTC) if isinstance(v, datetime) else v
               for k, v in params.items()})
        for sql, params in statements
    ]


def _naive_utc(value) -> datetime:
    """SQLite возвращает строку без пояса, PostgreSQL — datetime с поясом."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value


def _expected(dialect: str) -> dict[int, tuple[int, datetime]]:
    if dialect == "sqlite":
        return {
            100: (1, T0 + timedelta(minutes=30)),
            300: (1, T0 + timedelta(minutes=1)),
            500: (5, T0 + timedelta(minutes=10)),
        }
    # Получатель trial, удалённый до миграции, на PostgreSQL неизвестен.
    return {100: (1, T0 + timedelta(minutes=1))}


async def _refused(url: str, telegram_id: int) -> bool:
    engine = create_async_engine(url)
    try:
        async with AsyncSession(engine) as session:
            return await billing.trial_already_used(session, User(telegram_id=telegram_id))
    finally:
        await engine.dispose()


def _urls():
    yield pytest.param("sqlite", id="sqlite")
    yield pytest.param(
        "postgresql",
        id="postgresql",
        marks=pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set"),
    )


@pytest.mark.parametrize("dialect", _urls())
def test_migration_keeps_existing_trial_facts(tmp_path, monkeypatch, dialect):
    if dialect == "sqlite":
        url = f"sqlite+aiosqlite:///{tmp_path / 'migrate.sqlite3'}"
        seed = _seed_sqlite()
    else:
        url = PG_URL
        asyncio.run(_execute(url, ("DROP SCHEMA public CASCADE", {}),
                             ("CREATE SCHEMA public", {})))
        seed = _seed_postgres()
    config = _alembic(monkeypatch, url)
    try:
        command.upgrade(config, BEFORE)
        asyncio.run(_execute(url, *seed))

        command.upgrade(config, "head")

        rows = asyncio.run(_fetch(
            url, "SELECT telegram_id, user_id, granted_at FROM trial_grants"
        ))
        grants = {tg: (user_id, _naive_utc(at)) for tg, user_id, at in rows}
        assert grants == _expected(dialect)

        # Приложение после миграции отклоняет trial для этих Telegram ID.
        for telegram_id in _expected(dialect):
            assert asyncio.run(_refused(url, telegram_id))
        assert not asyncio.run(_refused(url, 200))
        assert not asyncio.run(_refused(url, 600))

        # Миграция обратима.
        command.downgrade(config, BEFORE)
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()
