"""Миграция ``subscription_purchases`` переносит сохранившиеся оплаты подписки.

SQLite проверяется всегда; PostgreSQL — при ``VPNBOT_TEST_PG_URL`` (отдельная
тестовая база: схема ``public`` пересоздаётся).
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.db.models import User
from app.services import billing
from tests.test_trial_grants_migration import (
    _alembic,
    _audit,
    _execute,
    _fetch,
    _naive_utc,
    _reset_audit,
    _user,
)
from tests.test_whitelist_pg import PG_URL

BEFORE = "d1e2f3a4b5c7"
T0 = datetime(2026, 9, 1, 12, 0)


def _at(minutes):
    return None if minutes is None else T0 + timedelta(minutes=minutes)


def _payment(payment_id, user_id, status, *, kind="subscription", applied=None,
             confirmed=None, created=0):
    return (
        "INSERT INTO payment_requests (id, user_id, amount, currency, period_days, kind,"
        " status, payment_code, created_at, confirmed_at, applied_at) VALUES (:id, :user,"
        " 175, 'RUB', :days, :kind, :status, :code, :created, :confirmed, :applied)",
        {
            "id": payment_id, "user": user_id, "kind": kind, "status": status,
            "days": 0 if kind == "traffic" else 30, "code": f"P-{payment_id}",
            "created": _at(created), "confirmed": _at(confirmed), "applied": _at(applied),
        },
    )


def _seed() -> list[tuple[str, dict]]:
    return [
        _user(1, 100, False),
        _user(2, 200, False),
        _user(3, None, False),
        _user(4, 400, False),
        _user(5, 500, False),
        # tg 100: самая ранняя применённая подписка — заявка 11.
        _payment(10, 1, "APPLIED", kind="traffic", applied=1),
        _payment(11, 1, "APPLIED", applied=5, confirmed=4),
        _payment(12, 1, "APPLIED", applied=50, confirmed=49),
        _payment(13, 1, "REJECTED"),
        # tg 200: заявка ещё не применена или не принята — не переносится.
        _payment(20, 2, "CONFIRMED", confirmed=3),
        _payment(21, 2, "FAILED", confirmed=6),
        _payment(22, 2, "WAITING_ADMIN"),
        # Пользователь только сайта: Telegram ID нет.
        _payment(30, 3, "APPLIED", applied=7),
        # tg 400: только покупка трафика.
        _payment(40, 4, "APPLIED", kind="traffic", applied=8),
        # tg 500: старая запись без applied_at — момент берётся из confirmed_at.
        _payment(50, 5, "APPLIED", confirmed=9),
        # tg 900: оплатил и сбросил бота до миграции — заявка удалена, в аудите
        # остались только id заявки и администратор. Принадлежность не угадывается.
        _user(9, 900, False),
        _payment(90, 9, "APPLIED", applied=10),
        _audit("billing.applied", None, 90, {"new_expires_at": "2026-10-01"}, 10),
        _reset_audit(9, 900, 11),
        ("DELETE FROM payment_requests WHERE user_id = 9", {}),
        ("DELETE FROM users WHERE id = 9", {}),
    ]


def _expected() -> dict[int, tuple[int, int, datetime]]:
    return {100: (1, 11, _at(5)), 500: (5, 50, _at(9))}


def _with_utc(statements):
    """timestamptz: явный UTC, независимо от часового пояса сервера."""
    return [
        (sql, {k: v.replace(tzinfo=UTC) if isinstance(v, datetime) else v
               for k, v in params.items()})
        for sql, params in statements
    ]


async def _trial_open(url: str, telegram_id: int) -> bool:
    engine = create_async_engine(url)
    try:
        async with AsyncSession(engine) as session:
            user = User(telegram_id=telegram_id)
            return not await billing.subscription_already_purchased(session, user)
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
def test_migration_keeps_applied_subscription_payments(tmp_path, monkeypatch, dialect):
    if dialect == "sqlite":
        url = f"sqlite+aiosqlite:///{tmp_path / 'migrate.sqlite3'}"
        seed = _seed()
    else:
        url = PG_URL
        asyncio.run(_execute(url, ("DROP SCHEMA public CASCADE", {}),
                             ("CREATE SCHEMA public", {})))
        seed = _with_utc(_seed())
    config = _alembic(monkeypatch, url)
    try:
        command.upgrade(config, BEFORE)
        asyncio.run(_execute(url, *seed))

        command.upgrade(config, "head")

        rows = asyncio.run(_fetch(
            url,
            "SELECT telegram_id, user_id, payment_request_id, paid_at"
            " FROM subscription_purchases",
        ))
        purchases = {tg: (user_id, pid, _naive_utc(at)) for tg, user_id, pid, at in rows}
        assert purchases == _expected()

        # После миграции правило закрыто по Telegram ID даже без заявок пользователя.
        assert not asyncio.run(_trial_open(url, 100))
        assert not asyncio.run(_trial_open(url, 500))
        for telegram_id in (200, 400, 900):
            assert asyncio.run(_trial_open(url, telegram_id))

        # Миграция обратима и повторяема; trial_grants не затрагивается.
        command.downgrade(config, BEFORE)
        assert asyncio.run(_fetch(url, "SELECT count(*) FROM trial_grants")) == [(0,)]
        command.upgrade(config, "head")
        rows = asyncio.run(_fetch(url, "SELECT telegram_id FROM subscription_purchases"))
        assert sorted(tg for (tg,) in rows) == [100, 500]
    finally:
        get_settings.cache_clear()
