"""Перенос на новую цель при конкурентных покупке, продлении, очереди и сверке (PostgreSQL).

Запуск — как ``tests/test_whitelist_pg.py`` (``VPNBOT_TEST_PG_URL``, отдельная тестовая
база; схема пересоздаётся). In-process asyncio.Lock подменён: операции сериализуются
только PostgreSQL advisory lock, как в разных процессах.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from sqlalchemy import func, select

from app.db.enums import PaymentStatus, Protocol
from app.db.models import PaymentRequest, ServerInbound, WhitelistLedger, WhitelistPlacement
from app.services import provisioning, whitelist
from tests.test_whitelist_pg import (  # noqa: F401
    PG_URL,
    SlowPanel,
    _confirm,
    _state,
    _subscription_request,
    pg,
    pytestmark,
)
from tests.whitelist_inbounds import vless_reality

GIB = whitelist.GIB


class SlowMovePanel(SlowPanel):
    async def detach_quota_client(self, server, email, inbound_ids):
        await asyncio.sleep(0.05)
        return await super().detach_quota_client(server, email, inbound_ids)


async def _retarget(maker, ids, monkeypatch, inbound_id: int) -> None:
    async def fetch(*_args, **_kwargs):
        return [vless_reality(i) for i in (7, 8, 9)]

    monkeypatch.setattr(provisioning, "fetch_inbounds", fetch)
    async with maker() as session:
        exists = await session.scalar(
            select(ServerInbound.id).where(
                ServerInbound.server_id == ids["wl"], ServerInbound.inbound_id == inbound_id
            )
        )
        if exists is None:
            session.add(ServerInbound(server_id=ids["wl"], inbound_id=inbound_id,
                                      protocol=Protocol.VLESS, enabled=False))
            await session.commit()
        server = await whitelist.get_active_server(session)
        assert server is not None
        result = await whitelist.choose_inbound(session, server, inbound_id, None)
        assert result.status == whitelist.INVENTORY_READY


async def _queue(maker, panel):
    async with maker() as session:
        return await whitelist.process_due(session, panel)


async def _reconcile(maker, panel):
    async with maker() as session:
        return await whitelist.reconcile_usage(session, panel)


async def _placement(maker, ids):
    async with maker() as session:
        rows = (
            await session.scalars(
                select(WhitelistPlacement).where(WhitelistPlacement.user_id == ids["user"])
            )
        ).all()
        account = await whitelist.get_account(session, ids["user"])
        return (
            sorted((r.inbound_id, r.state) for r in rows),
            (account.placement_inbound_id, account.placement_flow),
        )


async def test_move_racing_purchase_renewal_queue_and_reconcile(pg, monkeypatch):  # noqa: F811
    maker, ids = pg
    panel = SlowMovePanel()
    first = await _subscription_request(maker, ids["user"])
    await _confirm(maker, first, panel)
    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    assert state.inbound_ids == [7]
    panel.consume(ids["wl"], "PUBPG", 3 * GIB)
    await _retarget(maker, ids, monkeypatch, 8)
    async with maker() as session:
        renewal = PaymentRequest(user_id=ids["user"], amount=175, period_days=30,
                                 payment_code="PAY-SUB-MV", status=PaymentStatus.WAITING_ADMIN)
        purchase = PaymentRequest(
            user_id=ids["user"], amount=99, period_days=0, kind="traffic",
            traffic_bytes=25 * GIB, payment_code="PAY-TR-MV",
            status=PaymentStatus.WAITING_ADMIN,
        )
        session.add_all([renewal, purchase])
        await session.commit()
        renewal_id, purchase_id = renewal.id, purchase.id

    results = await asyncio.gather(
        _queue(maker, panel), _confirm(maker, renewal_id, panel),
        _confirm(maker, purchase_id, panel), _queue(maker, panel),
        _reconcile(maker, panel), _confirm(maker, purchase_id, panel),
    )
    confirmations = [r for r in results if hasattr(r, "applied")]
    assert sum(r.applied for r in confirmations) == 2
    await _queue(maker, panel)

    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    account, client, ledger = await _state(maker, ids)
    assert state.inbound_ids == [8] and state.enable
    assert state.used_bytes == 3 * GIB  # счётчик перенесён без сброса
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 25 * GIB)
    assert state.total_bytes == 3 * GIB + 35 * GIB
    assert client.expires_at == ids["expires"] + timedelta(days=60)
    async with maker() as session:
        grants = await session.scalar(
            select(func.count(WhitelistLedger.id)).where(WhitelistLedger.kind == "free_grant")
        )
        purchases = await session.scalar(
            select(func.count(WhitelistLedger.id)).where(WhitelistLedger.kind == "purchase")
        )
    assert (grants, purchases) == (2, 1)
    assert await _placement(maker, ids) == ([(8, "attached")], (8, ""))
    assert sorted(ids for *_, ids in panel.detached) == [(7,)]


async def test_concurrent_queues_during_retarget_converge_on_latest_target(
    pg, monkeypatch  # noqa: F811
):
    maker, ids = pg
    panel = SlowMovePanel()
    first = await _subscription_request(maker, ids["user"])
    await _confirm(maker, first, panel)
    await _retarget(maker, ids, monkeypatch, 8)

    async def retarget_to_nine():
        await asyncio.sleep(0.03)
        await _retarget(maker, ids, monkeypatch, 9)

    await asyncio.gather(_queue(maker, panel), retarget_to_nine(), _queue(maker, panel))
    for _ in range(3):  # очередь доводит перенос до последней цели
        await _queue(maker, panel)
    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    assert state.inbound_ids == [9]
    assert await _placement(maker, ids) == ([(9, "attached")], (9, ""))
    account, _, _ = await _state(maker, ids)
    assert account.applied_version == account.desired_version
    assert state.total_bytes == 10 * GIB
