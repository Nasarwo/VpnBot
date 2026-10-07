"""Одноразовый trial при параллельных запросах и сбросе бота на PostgreSQL.

Запуск: VPNBOT_TEST_PG_URL=postgresql+asyncpg://user@/db?host=/run/... pytest
База должна быть отдельной тестовой: схема пересоздаётся каждым тестом.
In-process asyncio.Lock подменяется (фикстура ``pg``): запросы сериализуются
только advisory lock и блокировками строк PostgreSQL, как в разных процессах.
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select

from app.db.enums import Protocol
from app.db.models import Server, ServerInbound, TrialGrant, User
from app.services import billing
from app.services.billing import BillingError
from tests.test_user_reset_pg import DONE, _reset
from tests.test_whitelist_pg import PG_URL, SlowPanel, pg  # noqa: F401

pytestmark = pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set")

TELEGRAM_ID = 77  # пользователь фикстуры pg


async def _trial(maker, user_id, panel):
    async with maker() as session:
        try:
            return await billing.grant_trial(session, user_id, panel, period_days=3)
        except BillingError:
            return None  # пользователь уже удалён сбросом


class _SlowProvisionPanel(SlowPanel):
    async def provision_server(self, server, spec, expiry_ms):
        await asyncio.sleep(0.05)
        await super().provision_server(server, spec, expiry_ms)


async def _import_std_inbound(maker) -> None:
    """Новый пользователь после сброса получает профиль через mock, а не импорт с панели."""
    async with maker() as session:
        std = await session.scalar(select(Server).where(Server.name == "std"))
        session.add(ServerInbound(server_id=std.id, inbound_id=1, protocol=Protocol.VLESS))
        await session.commit()


async def _grants(maker) -> list[TrialGrant]:
    async with maker() as session:
        return (await session.scalars(select(TrialGrant))).all()


async def test_parallel_trial_requests_grant_once(pg):  # noqa: F811
    maker, ids = pg
    panel = SlowPanel()

    results = await asyncio.gather(*(_trial(maker, ids["user"], panel) for _ in range(3)))

    assert sorted(r.applied for r in results) == [False, False, True]
    assert sum(r.already_used for r in results) == 2
    assert len(panel.calls) == 1  # один сервер, одно продление
    [grant] = await _grants(maker)
    assert (grant.telegram_id, grant.user_id) == (TELEGRAM_ID, ids["user"])


@pytest.mark.parametrize("first", ["trial", "reset"])
async def test_trial_racing_reset_is_granted_once_per_telegram_id(
    pg, first  # noqa: F811
):
    maker, ids = pg
    await _import_std_inbound(maker)
    panel = _SlowProvisionPanel()
    trial = _trial(maker, ids["user"], panel)
    reset = _reset(maker, ids["user"])
    if first == "trial":
        task = asyncio.create_task(trial)
        await asyncio.sleep(0.02)
        result, callback = await asyncio.gather(task, reset)
    else:
        task = asyncio.create_task(reset)
        await asyncio.sleep(0.02)
        callback, result = await asyncio.gather(task, trial)
    assert callback.alerts[-1] == DONE

    async with maker() as session:
        fresh = await session.scalar(select(User).where(User.telegram_id == TELEGRAM_ID))
    again = await _trial(maker, fresh.id, panel)

    applied = [r for r in (result, again) if r is not None and r.applied]
    assert len(applied) == 1
    if first == "trial":
        assert result.applied and again.already_used
    else:
        assert result is None and again.applied
    # Одна идентичность на панели: второй профиль не создан.
    assert len({email for _, email, _ in panel.provisioned}) == 1
    async with maker() as session:
        assert await session.scalar(select(func.count()).select_from(TrialGrant)) == 1
