"""Конкуренция операций услуги на PostgreSQL (SQLite не доказывает блокировки).

Запуск: VPNBOT_TEST_PG_URL=postgresql+asyncpg://user@/db?host=/run/... pytest
База должна быть отдельной тестовой: схема пересоздаётся каждым тестом.
In-process asyncio.Lock подменяется, чтобы каждая операция вела себя как
отдельный процесс и сериализовалась только PostgreSQL advisory lock.
"""
from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.enums import AttachmentType, PaymentStatus, Protocol, UserRole
from app.db.models import (
    ClientServerMapping,
    PaymentRequest,
    Server,
    ServerInbound,
    TrafficPackage,
    User,
    VpnClient,
    WhitelistLedger,
)
from app.services import billing, operation_lock, payments, whitelist
from app.services.panel_updater import MockPanelUpdater

PG_URL = os.environ.get("VPNBOT_TEST_PG_URL")
pytestmark = pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set")
GIB = whitelist.GIB


class _NoLocalLocks(dict):
    """Каждый вызов получает новый asyncio.Lock — как в отдельном процессе."""

    def setdefault(self, key, default=None):  # noqa: ARG002
        return asyncio.Lock()


class SlowPanel(MockPanelUpdater):
    """Модель панели с задержками, чтобы операции перекрывались во времени."""

    async def update_expiry(self, server, mapping, expiry_ms):
        await asyncio.sleep(0.05)
        await super().update_expiry(server, mapping, expiry_ms)

    async def apply_quota_client(self, server, spec, target):
        await asyncio.sleep(0.05)
        return await super().apply_quota_client(server, spec, target)

    async def read_quota_client(self, server, email):
        await asyncio.sleep(0.02)
        return await super().read_quota_client(server, email)


@pytest_asyncio.fixture
async def pg(monkeypatch):
    monkeypatch.setattr(operation_lock, "_locks", _NoLocalLocks())
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        user = User(telegram_id=77, username="u", first_name="U", role=UserRole.USER,
                    public_id="PUBPG")
        std = Server(name="std", panel_url="https://std", username="a", password="b")
        wl = Server(name="wl", panel_url="https://wl", username="a", password="b",
                    purpose="whitelist", inventory_status="ready")
        session.add_all([user, std, wl])
        await session.flush()
        session.add(ServerInbound(server_id=wl.id, inbound_id=7, protocol=Protocol.VLESS))
        client = VpnClient(user_id=user.id, email="PUBPG", is_active=True,
                           expires_at=datetime.now(UTC) + timedelta(days=10))
        session.add(client)
        await session.flush()
        session.add(ClientServerMapping(vpn_client_id=client.id, server_id=std.id,
                                        inbound_id=1, protocol=Protocol.VLESS,
                                        client_uuid="uuid", email="PUBPG"))
        await session.commit()
        await whitelist.ensure_defaults(session)
        config = await whitelist.get_config(session)
        config.service_enabled = True
        await session.commit()
        ids = {"user": user.id, "client": client.id, "wl": wl.id,
               "expires": client.expires_at}
    yield maker, ids
    await engine.dispose()


async def _traffic_request(maker, user_id, size_gb):
    async with maker() as session:
        package = await session.scalar(
            select(TrafficPackage).where(TrafficPackage.traffic_bytes == size_gb * GIB)
        )
        payment = await payments.create_traffic_request(session, user_id, package.id)
        await payments.attach_proof(session, payment.id, AttachmentType.TEXT, caption="ok")
        # Следующая заявка того же пользователя создаётся после решения по этой.
        return payment.id


async def _subscription_request(maker, user_id, days=30):
    async with maker() as session:
        payment = await payments.create_request(session, user_id, 175, days)
        return payment.id


async def _confirm(maker, payment_id, panel):
    async with maker() as session:
        return await billing.confirm_payment(session, payment_id, None, panel)


async def _state(maker, ids):
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
        client = await session.get(VpnClient, ids["client"])
        ledger = await session.scalar(select(func.count(WhitelistLedger.id)))
        return account, client, ledger


async def test_concurrent_renewal_and_purchase_lose_nothing(pg):
    maker, ids = pg
    panel = SlowPanel()
    sub_id = await _subscription_request(maker, ids["user"])
    # Покупка оформляется отдельной заявкой: создаём её после квитанции подписки.
    async with maker() as session:
        await payments.attach_proof(session, sub_id, AttachmentType.TEXT, caption="ok")
    async with maker() as session:
        package = await session.scalar(
            select(TrafficPackage).where(TrafficPackage.traffic_bytes == 25 * GIB)
        )
        traffic = PaymentRequest(
            user_id=ids["user"], amount=99, period_days=0, kind="traffic",
            traffic_bytes=package.traffic_bytes, traffic_package_id=package.id,
            payment_code="PAY-TRAFFIC", status=PaymentStatus.WAITING_ADMIN,
        )
        session.add(traffic)
        await session.commit()
        traffic_id = traffic.id
    results = await asyncio.gather(
        _confirm(maker, sub_id, panel), _confirm(maker, traffic_id, panel)
    )
    assert all(r.applied for r in results)
    account, client, ledger = await _state(maker, ids)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 25 * GIB)
    assert client.expires_at == ids["expires"] + timedelta(days=30)
    assert ledger == 2
    state = panel.quota_clients[(ids["wl"], "PUBPG")]
    assert state.total_bytes == 35 * GIB and state.enable
    assert account.applied_version == account.desired_version


async def test_two_purchases_and_double_click_credit_exactly_once_each(pg):
    maker, ids = pg
    panel = SlowPanel()
    first = await _traffic_request(maker, ids["user"], 10)
    async with maker() as session:
        package = await session.scalar(
            select(TrafficPackage).where(TrafficPackage.traffic_bytes == 25 * GIB)
        )
        second = PaymentRequest(
            user_id=ids["user"], amount=99, period_days=0, kind="traffic",
            traffic_bytes=package.traffic_bytes, payment_code="PAY-SECOND",
            status=PaymentStatus.WAITING_ADMIN,
        )
        session.add(second)
        await session.commit()
        second_id = second.id
    results = await asyncio.gather(
        _confirm(maker, first, panel),
        _confirm(maker, first, panel),  # двойное нажатие
        _confirm(maker, second_id, panel),
        _confirm(maker, second_id, panel),
    )
    assert sum(r.applied for r in results) == 2
    assert sum(r.already_applied for r in results) == 2
    account, _, ledger = await _state(maker, ids)
    assert account.paid_bytes == 35 * GIB
    assert ledger == 2
    assert panel.quota_clients[(ids["wl"], "PUBPG")].total_bytes == 35 * GIB


async def test_background_queue_racing_purchase_never_rolls_back(pg):
    maker, ids = pg
    panel = SlowPanel()
    down = SlowPanel(fail_server_ids={ids["wl"]})
    down.quota_clients = panel.quota_clients
    first = await _traffic_request(maker, ids["user"], 10)
    await _confirm(maker, first, down)  # начислено, применение отложено
    async with maker() as session:
        account = await whitelist.get_account(session, ids["user"])
        account.next_sync_at = None
        await session.commit()
    second = await _traffic_request(maker, ids["user"], 25)

    async def queue():
        async with maker() as session:
            return await whitelist.process_due(session, panel)

    await asyncio.gather(queue(), _confirm(maker, second, panel), queue())
    account, _, _ = await _state(maker, ids)
    assert account.paid_bytes == 35 * GIB
    assert panel.quota_clients[(ids["wl"], "PUBPG")].total_bytes == 35 * GIB
    assert account.applied_version == account.desired_version


async def test_concurrent_renewals_and_retry_extend_once_each(pg):
    maker, ids = pg
    panel = SlowPanel()
    first = await _subscription_request(maker, ids["user"])
    async with maker() as session:
        await payments.attach_proof(session, first, AttachmentType.TEXT, caption="ok")
        second = PaymentRequest(user_id=ids["user"], amount=850, period_days=180,
                                payment_code="PAY-SUB2", status=PaymentStatus.WAITING_ADMIN)
        session.add(second)
        await session.commit()
        second_id = second.id

    async def retry(payment_id):
        async with maker() as session:
            try:
                return await billing.retry_payment(session, payment_id, None, panel)
            except billing.BillingError:
                return None

    await asyncio.gather(
        _confirm(maker, first, panel), _confirm(maker, second_id, panel),
        retry(first), _confirm(maker, first, panel),
    )
    account, client, _ = await _state(maker, ids)
    assert client.expires_at == ids["expires"] + timedelta(days=210)
    async with maker() as session:
        grants = await session.scalar(
            select(func.count(WhitelistLedger.id)).where(WhitelistLedger.kind == "free_grant")
        )
    assert grants == 2 and account.free_bytes == 10 * GIB


async def test_outage_renewal_purchase_queue_and_reconcile_settle_once(pg):
    """Сбой статистики: параллельные продление, покупка, очередь и сверка."""
    maker, ids = pg
    panel = SlowPanel()
    first = await _subscription_request(maker, ids["user"])
    await _confirm(maker, first, panel)
    async with maker() as session:
        await whitelist.adjust_balance(
            session, ids["user"], free_bytes=2 * GIB, paid_bytes=15 * GIB,
            actor_user_id=None, reason="baseline", updater=panel,
        )
    panel.consume(ids["wl"], "PUBPG", 5 * GIB, at=datetime.now(UTC) - timedelta(minutes=40))
    panel.read_fail_server_ids.add(ids["wl"])
    async with maker() as session:
        renewal = PaymentRequest(user_id=ids["user"], amount=175, period_days=30,
                                 payment_code="PAY-SUB-OUT", status=PaymentStatus.WAITING_ADMIN)
        purchase = PaymentRequest(
            user_id=ids["user"], amount=99, period_days=0, kind="traffic",
            traffic_bytes=25 * GIB, payment_code="PAY-TR-OUT",
            status=PaymentStatus.WAITING_ADMIN,
        )
        session.add_all([renewal, purchase])
        await session.commit()
        renewal_id, purchase_id = renewal.id, purchase.id

    async def queue():  # как фоновый цикл main.py: сверка, затем очередь
        async with maker() as session:
            await whitelist.reconcile_usage(session, panel)
            await whitelist.process_due(session, panel)

    results = await asyncio.gather(
        _confirm(maker, renewal_id, panel), _confirm(maker, purchase_id, panel),
        _confirm(maker, renewal_id, panel), queue(),
    )
    assert sum(r.applied for r in results if r) == 2
    account, _, _ = await _state(maker, ids)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)

    panel.read_fail_server_ids.clear()
    await asyncio.gather(queue(), queue())
    account, client, _ = await _state(maker, ids)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 37 * GIB)
    assert client.expires_at == ids["expires"] + timedelta(days=60)
    async with maker() as session:
        rows = (await session.scalars(
            select(WhitelistLedger).where(WhitelistLedger.source_key.in_(
                [f"payment:{renewal_id}", f"payment:{purchase_id}"]
            ))
        )).all()
    assert sorted((r.status, r.anchor_bytes) for r in rows) == [("settled", 5 * GIB)] * 2
    assert panel.quota_clients[(ids["wl"], "PUBPG")].total_bytes == 5 * GIB + 47 * GIB
