"""Alembic: одна head, миграция пустой БД и обновление со схемы до исправлений.

Head проверяется всегда; PostgreSQL — при ``VPNBOT_TEST_PG_URL`` (отдельная
тестовая база: схема ``public`` пересоздаётся). «До исправлений» — ревизия
``a4b5c6d7e8f9``, head зафиксированного кода до таблиц ``trial_grants`` и
``subscription_purchases`` (ревью 2026-10-07).
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db.base import Base
from app.db.enums import PaymentStatus, Protocol, UserRole
from app.db.models import (
    ClientServerMapping,
    PaymentRequest,
    PendingServerUpdate,
    Server,
    SubscriptionPurchase,
    TrialGrant,
    User,
    VpnClient,
)
from app.services import billing, pending_updates, renewal_recovery
from app.services.panel_updater import MockPanelUpdater
from tests.test_trial_grants_migration import ROOT, _alembic
from tests.test_whitelist_pg import PG_URL

PRE_FIX = "a4b5c6d7e8f9"
FIX_REVISIONS = {"d1e2f3a4b5c7", "e3f4a5b6c7d8", "f4a5b6c7d8e9"}
pg_only = pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set")

# До миграции выравнивания ширина password в БД остаётся 512 вместо 1024.
PRE_FIX_DRIFT = {("modify_type", "servers.password")}


def _script() -> ScriptDirectory:
    from alembic.config import Config

    config = Config()
    config.set_main_option("script_location", str(ROOT / "app/migrations"))
    return ScriptDirectory.from_config(config)


def test_single_alembic_head_contains_fix_revisions():
    script = _script()
    heads = script.get_heads()
    assert len(heads) == 1
    chain = {revision.revision for revision in script.walk_revisions("base", heads[0])}
    assert FIX_REVISIONS <= chain and PRE_FIX in chain
    assert script.get_revision("d1e2f3a4b5c7").down_revision == PRE_FIX


def _drift_key(diff) -> tuple[str, str]:
    if isinstance(diff, list):  # modify_* приходят списком изменений столбца
        kind, _, table, column, *_ = diff[0]
        return kind, f"{table}.{column}"
    kind, obj = diff[0], diff[1]
    return kind, getattr(obj, "name", None) or str(obj)


async def _reset_schema() -> None:
    engine = create_async_engine(PG_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()


async def _drift() -> set[tuple[str, str]]:
    engine = create_async_engine(PG_URL)
    try:
        async with engine.connect() as conn:
            diffs = await conn.run_sync(lambda sync: compare_metadata(
                MigrationContext.configure(sync, opts={"compare_type": True}),
                Base.metadata,
            ))
    finally:
        await engine.dispose()
    return {_drift_key(diff) for diff in diffs}


@pg_only
def test_empty_postgresql_migrates_to_head_matching_models(monkeypatch):
    asyncio.run(_reset_schema())
    config = _alembic(monkeypatch, PG_URL)
    try:
        command.upgrade(config, "head")
        assert asyncio.run(_drift()) == set()
        # Откат исправлений и повторное применение.
        command.downgrade(config, PRE_FIX)
        assert asyncio.run(_drift()) == PRE_FIX_DRIFT | {
            ("add_table", "trial_grants"), ("add_table", "subscription_purchases"),
        }
        command.upgrade(config, "head")
        assert asyncio.run(_drift()) == set()
    finally:
        get_settings.cache_clear()


# --- Обновление со схемы до исправлений -------------------------------------------------------


async def _seed_pre_fix() -> dict:
    """Данные на схеме до исправлений: оплаченная подписка с отложенным обновлением.

    Исправления добавляют таблицы и расширяют password; исходные данные
    помещаются в прежнюю ширину и заполняются моделями приложения.
    """
    engine = create_async_engine(PG_URL)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    target = datetime.now(UTC).replace(microsecond=0) + timedelta(days=40)
    try:
        async with maker() as session:
            paid = User(telegram_id=501, username="p", first_name="P", role=UserRole.USER,
                        onboarding_done=True, public_id="PUB501")
            trial = User(telegram_id=502, username="t", first_name="T", role=UserRole.USER,
                         onboarding_done=True, public_id="PUB502", trial_used=True)
            fresh = User(telegram_id=503, username="f", first_name="F", role=UserRole.USER,
                         onboarding_done=True, public_id="PUB503")
            server = Server(name="std", panel_url="https://std", username="a", password="b",
                            enabled=True)
            session.add_all([paid, trial, fresh, server])
            await session.flush()
            client = VpnClient(user_id=paid.id, display_name="c", email="PUB501",
                               is_active=True, expires_at=target)
            session.add(client)
            await session.flush()
            session.add(ClientServerMapping(
                vpn_client_id=client.id, server_id=server.id, inbound_id=1,
                protocol=Protocol.VLESS, client_uuid="uuid-501", email="PUB501",
            ))
            payment = PaymentRequest(
                user_id=paid.id, amount=175, period_days=30, payment_code="PAY-501",
                status=PaymentStatus.APPLIED, target_expires_at=target,
                confirmed_at=target - timedelta(days=30),
                applied_at=target - timedelta(days=30),
                last_error="Отложено применение на серверы",
            )
            session.add(payment)
            await session.flush()
            session.add(PendingServerUpdate(
                vpn_client_id=client.id, server_id=server.id,
                payment_request_id=payment.id, target_expires_at=target,
                status="pending", attempts=2, last_error="timeout",
                next_retry_at=datetime.now(UTC) - timedelta(seconds=1),
            ))
            await session.commit()
            return {"paid": paid.id, "trial": trial.id, "fresh": fresh.id,
                    "server": server.id, "payment": payment.id, "target": target}
    finally:
        await engine.dispose()


async def _after_upgrade(ids: dict) -> dict:
    engine = create_async_engine(PG_URL)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    panel = MockPanelUpdater()
    try:
        async with maker() as session:
            report = await renewal_recovery.run_once(
                session, panel, backoff=pending_updates.RetryBackoff()
            )
        async with maker() as session:
            purchases = (await session.scalars(select(SubscriptionPurchase))).all()
            grants = (await session.scalars(select(TrialGrant))).all()
            available = {
                name: await billing.trial_available(session, await session.get(User, ids[name]))
                for name in ("paid", "trial", "fresh")
            }
            row = await session.scalar(select(PendingServerUpdate))
            payment = await session.get(PaymentRequest, ids["payment"])
        return {
            "report": report, "calls": panel.calls, "row": row, "payment": payment,
            "purchases": [(p.telegram_id, p.payment_request_id) for p in purchases],
            "grants": [g.telegram_id for g in grants], "available": available,
        }
    finally:
        await engine.dispose()


@pg_only
def test_pre_fix_postgresql_upgrades_and_recovery_worker_runs(monkeypatch):
    asyncio.run(_reset_schema())
    config = _alembic(monkeypatch, PG_URL)
    try:
        command.upgrade(config, PRE_FIX)
        ids = asyncio.run(_seed_pre_fix())
        command.upgrade(config, "head")
        state = asyncio.run(_after_upgrade(ids))
    finally:
        get_settings.cache_clear()

    # Факты перенесены: оплаченная подписка и использованный trial закрывают trial.
    assert state["purchases"] == [(501, ids["payment"])]
    assert state["grants"] == [502]
    assert state["available"] == {"paid": False, "trial": False, "fresh": True}
    # Отложенное обновление, созданное до исправлений, применяет новый worker.
    assert state["report"].updates_applied == 1
    assert state["calls"] == [(ids["server"], billing.expiry_to_ms(ids["target"]))]
    row = state["row"]
    assert (row.status, row.attempts, row.next_retry_at) == ("applied", 3, None)
    assert state["payment"].last_error is None
