"""Оплата подписки, сброс бота и trial конкурентно на PostgreSQL.

Запуск: VPNBOT_TEST_PG_URL=postgresql+asyncpg://user@/db?host=/run/... pytest
База должна быть отдельной тестовой: схема пересоздаётся каждым тестом.
In-process asyncio.Lock подменяется (фикстура ``pg``): операции сериализуются
только advisory lock и блокировками строк PostgreSQL, как в разных процессах.
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import func, select

from app.bot import texts
from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest, SubscriptionPurchase, TrialGrant, User
from app.services.user_reset import ResetBlock
from tests.test_trial_reset_pg import TELEGRAM_ID, _import_std_inbound, _SlowProvisionPanel, _trial
from tests.test_user_reset_pg import (
    DONE,
    _confirm,
    _pause_after_check,
    _reset,
    _subscription_payment,
)
from tests.test_whitelist_pg import PG_URL, SlowPanel, pg  # noqa: F401

pytestmark = pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set")


async def _fresh_id(maker) -> int:
    async with maker() as session:
        return await session.scalar(select(User.id).where(User.telegram_id == TELEGRAM_ID))


async def _counts(maker) -> tuple[int, int]:
    async with maker() as session:
        return (
            await session.scalar(select(func.count()).select_from(SubscriptionPurchase)),
            await session.scalar(select(func.count()).select_from(TrialGrant)),
        )


@pytest.mark.parametrize("first", ["confirm", "reset"])
async def test_payment_confirmation_racing_reset_keeps_trial_closed(
    pg, monkeypatch, first  # noqa: F811
):
    maker, ids = pg
    panel = SlowPanel()
    payment_id = await _subscription_payment(maker, ids["user"])
    entered = _pause_after_check(monkeypatch)

    if first == "reset":
        reset = asyncio.create_task(_reset(maker, ids["user"]))
        await asyncio.wait_for(entered.wait(), 5)
        confirm = asyncio.create_task(_confirm(maker, payment_id, panel))
    else:
        confirm = asyncio.create_task(_confirm(maker, payment_id, panel))
        await asyncio.sleep(0.02)
        reset = asyncio.create_task(_reset(maker, ids["user"]))
    callback, result = await asyncio.gather(reset, confirm)

    assert result.applied
    if first == "reset":
        # Сброс видел ожидающую заявку и был отклонён; пользователь сбрасывает снова.
        assert callback.alerts[-1] == texts.reset_blocked(ResetBlock.OPEN_PAYMENT)
        callback = await _reset(maker, ids["user"])
    assert callback.alerts[-1] == DONE
    async with maker() as session:
        assert await session.get(PaymentRequest, payment_id) is None
    fresh_id = await _fresh_id(maker)
    assert fresh_id != ids["user"]

    trial_panel = _SlowProvisionPanel()
    refused = await _trial(maker, fresh_id, trial_panel)

    assert not refused.applied and refused.subscription_purchased
    assert trial_panel.provisioned == [] and trial_panel.calls == []
    assert await _counts(maker) == (1, 0)


async def test_parallel_trials_after_paid_reset_are_all_refused(pg):  # noqa: F811
    maker, ids = pg
    await _confirm(maker, await _subscription_payment(maker, ids["user"]), SlowPanel())
    assert (await _reset(maker, ids["user"])).alerts[-1] == DONE
    await _import_std_inbound(maker)
    fresh_id = await _fresh_id(maker)
    panel = _SlowProvisionPanel()

    results = await asyncio.gather(*(_trial(maker, fresh_id, panel) for _ in range(3)))

    assert all(not r.applied and r.subscription_purchased for r in results)
    assert panel.provisioned == []
    assert await _counts(maker) == (1, 0)


@pytest.mark.parametrize("first", ["trial", "confirm"])
async def test_trial_racing_payment_then_reset(pg, first):  # noqa: F811
    """Trial до оплаты разрешён; после оплаты и сброса trial закрыт в обоих порядках."""
    maker, ids = pg
    payment_id = await _subscription_payment(maker, ids["user"])
    panel = SlowPanel()
    if first == "trial":
        trial = asyncio.create_task(_trial(maker, ids["user"], panel))
        await asyncio.sleep(0.02)
        confirmed = await _confirm(maker, payment_id, panel)
        granted = await trial
    else:
        confirm = asyncio.create_task(_confirm(maker, payment_id, panel))
        await asyncio.sleep(0.02)
        granted = await _trial(maker, ids["user"], panel)
        confirmed = await confirm

    assert confirmed.applied
    async with maker() as session:
        status = await session.scalar(
            select(PaymentRequest.status).where(PaymentRequest.id == payment_id)
        )
    assert status == PaymentStatus.APPLIED
    if first == "trial":
        assert granted.applied
        assert await _counts(maker) == (1, 1)
    else:
        assert not granted.applied and granted.subscription_purchased
        assert await _counts(maker) == (1, 0)

    assert (await _reset(maker, ids["user"])).alerts[-1] == DONE
    again = await _trial(maker, await _fresh_id(maker), _SlowProvisionPanel())
    assert not again.applied
    assert again.already_used if first == "trial" else again.subscription_purchased


async def test_concurrent_confirmations_record_one_purchase(pg):  # noqa: F811
    """Две заявки одного пользователя подтверждаются параллельно: одна запись."""
    maker, ids = pg
    first_id = await _subscription_payment(maker, ids["user"])
    async with maker() as session:
        # Вторая заявка той же подписки (create_request не даёт двух открытых).
        first = await session.get(PaymentRequest, first_id)
        second = PaymentRequest(
            user_id=ids["user"], amount=first.amount, period_days=30,
            status=PaymentStatus.WAITING_ADMIN, payment_code="PG-SECOND",
        )
        session.add(second)
        await session.commit()
        second_id = second.id
    panel = SlowPanel()

    results = await asyncio.gather(
        _confirm(maker, first_id, panel), _confirm(maker, second_id, panel)
    )

    assert all(r.applied for r in results)
    async with maker() as session:
        [purchase] = (await session.scalars(select(SubscriptionPurchase))).all()
    assert purchase.telegram_id == TELEGRAM_ID
    assert purchase.payment_request_id in {first_id, second_id}
