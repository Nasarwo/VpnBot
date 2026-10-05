"""Приёмка: гонки услуги на PostgreSQL, не покрытые test_whitelist_pg.

Те же условия, что в test_whitelist_pg: отдельная тестовая база
(VPNBOT_TEST_PG_URL), схема пересоздаётся, in-process блокировки отключены —
операции сериализуются только advisory lock PostgreSQL, как в разных процессах.
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.db.enums import PaymentStatus
from app.db.models import PaymentRequest, User, VpnClient, WhitelistLedger
from app.services import billing, whitelist
from tests.test_whitelist_pg import (  # noqa: F401
    GIB,
    SlowPanel,
    _confirm,
    _traffic_request,
    pg,
    pytestmark,  # noqa: F401
)


async def _ledger(maker, kind: str | None = None) -> int:
    async with maker() as session:
        query = select(func.count(WhitelistLedger.id))
        if kind:
            query = query.where(WhitelistLedger.kind == kind)
        return await session.scalar(query)


async def test_trial_double_click_grants_three_gb_once(pg):  # noqa: F811
    maker, ids = pg
    panel = SlowPanel()

    async def trial():
        async with maker() as session:
            return await billing.grant_trial(session, ids["user"], panel, period_days=3)

    results = await asyncio.gather(trial(), trial(), trial())
    assert sum(r.applied for r in results) == 1
    assert sum(r.already_used for r in results) == 2
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
        client = await session.get(VpnClient, ids["client"])
        user = await session.get(User, ids["user"])
    assert user.trial_used
    assert account.free_bytes == 3 * GIB and account.paid_bytes == 0
    assert client.expires_at == ids["expires"] + timedelta(days=3)
    assert await _ledger(maker, whitelist.LEDGER_FREE_GRANT) == 1
    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    assert state.total_bytes == 3 * GIB and state.enable


async def test_concurrent_rollouts_grant_once_and_keep_purchase(pg):  # noqa: F811
    maker, ids = pg
    panel = SlowPanel()
    async with maker() as session:
        config = await whitelist.get_config(session)
        config.service_enabled = False
        session.add(PaymentRequest(
            user_id=ids["user"], amount=175, period_days=30, payment_code="PAY-OLD-PG",
            status=PaymentStatus.APPLIED, target_expires_at=ids["expires"],
        ))
        await session.commit()

    async def rollout(include_ambiguous: bool):
        async with maker() as session:
            return await whitelist.run_rollout(
                session, panel, include_ambiguous=include_ambiguous, actor_user_id=None
            )

    reports = await asyncio.gather(rollout(False), rollout(True), rollout(False))
    assert sum(r.granted.get("paid", 0) for r in reports) == 1
    assert sum(r.skipped_existing for r in reports) == 2
    assert await _ledger(maker, whitelist.LEDGER_ROLLOUT) == 1

    # Покупка после запуска и повторные запуски не обнуляют купленный остаток.
    purchase = await _traffic_request(maker, ids["user"], 25)
    await asyncio.gather(_confirm(maker, purchase, panel), rollout(True), rollout(False))
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 25 * GIB)
    assert await _ledger(maker, whitelist.LEDGER_ROLLOUT) == 1
    assert panel.quota_clients[(ids["wl"], "PUBPG")].total_bytes == 35 * GIB


async def test_admin_block_is_not_lost_to_queue_reads_or_reconcile(pg):  # noqa: F811
    maker, ids = pg
    panel = SlowPanel()
    purchase = await _traffic_request(maker, ids["user"], 10)
    await _confirm(maker, purchase, panel)
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
        # Очередь видит несинхронизированное состояние одновременно с блокировкой.
        whitelist.mark_dirty(account)
        await session.commit()

    async def block():
        async with maker() as session:
            return await whitelist.set_admin_block(session, ids["user"], True, None, panel)

    async def queue():
        async with maker() as session:
            return await whitelist.process_due(session, panel)

    async def read():
        async with maker() as session:
            return await whitelist.user_overview(session, ids["user"], panel)

    async def reconcile():
        async with maker() as session:
            return await whitelist.reconcile_cycle(session, panel, pause_seconds=0)

    await asyncio.gather(queue(), block(), read(), reconcile(), queue(), read())
    await asyncio.gather(queue(), read(), reconcile())
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
    assert account.admin_blocked and account.applied_enable is False
    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    assert state.enable is False and state.total_bytes == 10 * GIB
    overview = await read()
    assert overview.status == whitelist.STATUS_BLOCKED and overview.paid_bytes == 10 * GIB


async def test_purchase_confirmed_after_expiry_races_queue_without_enabling(pg):  # noqa: F811
    maker, ids = pg
    panel = SlowPanel()
    first = await _traffic_request(maker, ids["user"], 10)
    await _confirm(maker, first, panel)  # конфиг создан и включён при активной подписке
    assert panel.quota_clients[(ids["wl"], "PUBPG")].enable
    purchase = await _traffic_request(maker, ids["user"], 25)
    async with maker() as session:
        client = await session.get(VpnClient, ids["client"])
        client.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await session.commit()

    async def queue():
        async with maker() as session:
            return await whitelist.process_due(session, panel)

    results = await asyncio.gather(
        _confirm(maker, purchase, panel), _confirm(maker, purchase, panel), queue(), queue()
    )
    confirmations = [r for r in results if isinstance(r, billing.BillingResult)]
    assert sum(r.applied for r in confirmations) == 1
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
    assert account.paid_bytes == 35 * GIB
    assert await _ledger(maker, whitelist.LEDGER_PURCHASE) == 2
    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    # Истёкшая подписка: начисление сохранено, конфиг выключен, квота конечна.
    assert state.enable is False and state.total_bytes == 35 * GIB
    assert state.expiry_ms <= int(datetime.now(UTC).timestamp() * 1000)
