"""Восстановление обычных VPN-продлений не зависит от проверки здоровья серверов.

Дефект (ревью 2026-10-07, P2): ``recover_confirmed_payments`` и очередь
отложенных обновлений обычных серверов обслуживались только внутри
``_server_health_poller``; при ``SERVER_HEALTH_POLL_SECONDS=0`` оплата во время
недоступности панели не доходила до панели, а прерванное рестартом подтверждение
(``CONFIRMED``) не возобновлялось без администратора. Теперь их обслуживает
отдельный ``_renewal_recovery_worker``; проверка здоровья только сохраняет статус.

Панели — ``MockPanelUpdater`` (режим привязок: ``update_expiry``), БД — файловая
SQLite с отдельными соединениями теста и worker'а, SubHub — локальный HTTP-сервер.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import func, select

from app import main as app_main
from app.config import Settings
from app.db.enums import PaymentStatus, Protocol, UserRole
from app.db.models import (
    AuditLog,
    ClientServerMapping,
    PaymentRequest,
    PendingServerUpdate,
    Server,
    User,
    VpnClient,
)
from app.db.repositories import PaymentRepository, ServerRepository
from app.services import billing, health, pending_updates, renewal_recovery
from app.services.panel_updater import MockPanelUpdater
from tests.test_subhub_trigger import LocalSubHub
from tests.test_whitelist_queue_worker import _maker, _until, session  # noqa: F401

POLL = 0.02  # секунды: быстрый цикл worker'а в тестах


def _settings(**overrides) -> Settings:
    base: dict[str, Any] = {
        "anti_sharing_enabled": False,
        "expiry_notify_poll_seconds": 0,
        "server_health_poll_seconds": 0,
        "whitelist_reconcile_minutes": 0,
        "whitelist_queue_poll_seconds": POLL,
        "renewal_recovery_poll_seconds": POLL,
    }
    base.update(overrides)
    return Settings(**base)


@pytest.fixture
def wire(monkeypatch, session):  # noqa: F811
    """Фоновые задачи приложения — на БД теста, подменяемой панели и без сети health-check."""
    probes: list[int] = []

    async def fake_check_server(server, timeout: float = 10.0) -> bool:
        probes.append(server.id)
        return True

    def _wire(panel: MockPanelUpdater) -> list[int]:
        monkeypatch.setattr(app_main, "get_sessionmaker", lambda: _maker(session))
        monkeypatch.setattr(
            "app.services.whitelist_labels.get_sessionmaker", lambda: _maker(session)
        )
        monkeypatch.setattr(app_main, "build_updater", lambda **_: panel)
        monkeypatch.setattr(health, "check_server", fake_check_server)
        return probes

    return _wire


class _Crash(Exception):
    """Процесс «умер» посреди обращения к панели (не ошибка панели)."""


class _CrashingPanel(MockPanelUpdater):
    async def update_expiry(self, server, mapping, expiry_ms):
        raise _Crash("process killed")


class _HangingPanel(MockPanelUpdater):
    def __init__(self) -> None:
        super().__init__()
        self.entered = asyncio.Event()
        self.cancelled = asyncio.Event()

    async def update_expiry(self, server, mapping, expiry_ms):
        self.entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled.set()
            raise


@dataclass(frozen=True, slots=True)
class Ids:
    """Идентификаторы фикстур: объекты сессии теста истекают после rollback."""

    user: int
    client: int
    server: int


@pytest.fixture
def ids(user, vpn_client, server) -> Ids:
    return Ids(user=user.id, client=vpn_client.id, server=server.id)


async def _waiting_payment(db, user_id: int, code: str = "PAY-1", days: int = 30) -> int:
    payment = await PaymentRepository(db).create(
        user_id=user_id, amount=175, period_days=days, payment_code=code,
        status=PaymentStatus.WAITING_ADMIN,
    )
    await db.commit()
    return payment.id


async def _pay_during_outage(
    db, user_id: int, server_id: int, code: str = "PAY-1"
) -> tuple[int, datetime]:
    """Оплата подтверждена, пока панель недоступна: APPLIED + отложенное обновление."""
    payment_id = await _waiting_payment(db, user_id, code)
    down = MockPanelUpdater(fail_server_ids={server_id})
    result = await billing.confirm_payment(db, payment_id, None, down)
    assert result.applied and [r.server_id for r in result.failed_servers] == [server_id]
    return payment_id, billing._as_aware(result.new_expires_at)


async def _fresh(db, model, ident):
    return await db.get(model, ident, populate_existing=True)


async def _pending(db) -> list[PendingServerUpdate]:
    return list((await db.scalars(
        select(PendingServerUpdate)
        .order_by(PendingServerUpdate.id)
        .execution_options(populate_existing=True)
    )).all())


async def _audit_count(db, action: str) -> int:
    return await db.scalar(
        select(func.count()).select_from(AuditLog).where(AuditLog.action == action)
    )


async def _wait_pending_status(db, status: str, timeout: float = 5.0) -> None:
    async with asyncio.timeout(timeout):
        while True:
            rows = await _pending(db)
            if rows and all(row.status == status for row in rows):
                return
            await asyncio.sleep(0.01)


async def _wait_payment(db, payment_id: int, status: PaymentStatus) -> PaymentRequest:
    async with asyncio.timeout(5):
        while True:
            payment = await _fresh(db, PaymentRequest, payment_id)
            if payment.status == status:
                return payment
            await asyncio.sleep(0.01)


def _expiry_calls(panel: MockPanelUpdater, server_id: int) -> list[int]:
    return [ms for sid, ms in panel.calls if sid == server_id]


async def _second_user(db, server_id: int, telegram_id: int = 777) -> tuple[int, int]:
    user = User(telegram_id=telegram_id, username=f"u{telegram_id}", first_name="Second",
                role=UserRole.USER, onboarding_done=True)
    db.add(user)
    await db.flush()
    client = VpnClient(user_id=user.id, display_name="Second", email=f"{telegram_id}@local",
                       is_active=False, subscription_url_direct=f"https://sub/{telegram_id}")
    db.add(client)
    await db.flush()
    db.add(ClientServerMapping(
        vpn_client_id=client.id, server_id=server_id, inbound_id=1, protocol=Protocol.VLESS,
        client_uuid=f"uuid-{telegram_id}", email=f"{telegram_id}@local", enabled=True,
    ))
    await db.commit()
    return user.id, client.id


# --- Запуск ровно одного обработчика -------------------------------------------------------


@pytest.fixture
def started(monkeypatch):
    names: list[str] = []

    def fake(name: str):
        async def runner(*_args, **_kwargs) -> None:
            names.append(name)
            await asyncio.Event().wait()

        return runner

    for attr, name in (
        ("_anti_sharing_poller", "anti_sharing"),
        ("_server_health_poller", "health"),
        ("_whitelist_reconcile_poller", "reconcile"),
        ("_expiry_notify_poller", "expiry"),
        ("_whitelist_queue_worker", "queue"),
        ("_renewal_recovery_worker", "renewal"),
    ):
        monkeypatch.setattr(app_main, attr, fake(name))
    return names


@pytest.mark.parametrize("health_seconds", [0, 60])
async def test_recovery_worker_runs_once_regardless_of_health_polling(started, health_seconds):
    settings = _settings(server_health_poll_seconds=health_seconds)
    first = app_main.start_background_tasks(object(), settings)
    second = app_main.start_background_tasks(object(), settings)  # повторный запуск
    await asyncio.sleep(0)
    try:
        assert started.count("renewal") == 1
        assert started.count("queue") == 1
        assert started.count("health") == (2 if health_seconds else 0)
    finally:
        await app_main.stop_background_tasks(first + second)
    # После остановки worker можно запустить снова (перезапуск процесса).
    again = app_main.start_background_tasks(object(), _settings())
    await asyncio.sleep(0)
    try:
        assert started.count("renewal") == 2
    finally:
        await app_main.stop_background_tasks(again)


async def test_health_check_only_records_status(session, ids, wire):  # noqa: F811
    """Проверка здоровья больше не обрабатывает очередь: нет второго обработчика."""
    await _pay_during_outage(session, ids.user, ids.server)
    panel = MockPanelUpdater()
    probes = wire(panel)
    await health.check_servers(session, timeout=1.0)
    assert probes == [ids.server]
    assert panel.calls == []
    assert [row.status for row in await _pending(session)] == ["pending"]
    assert (await _fresh(session, Server, ids.server)).is_online is True


# --- Оплата при недоступной панели → восстановление без health polling ------------------------


@pytest.mark.parametrize("health_seconds", [0, 60])
async def test_payment_during_outage_reaches_panel_after_recovery(
    session, ids, wire, health_seconds  # noqa: F811
):
    payment_id, target = await _pay_during_outage(session, ids.user, ids.server)
    panel = MockPanelUpdater()
    probes = wire(panel)
    async with LocalSubHub() as hub:
        settings = _settings(
            server_health_poll_seconds=health_seconds, subhub_url=hub.url,
            subhub_admin_token="admin-secret", subhub_timeout_seconds=2,
        )
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _wait_pending_status(session, "applied")
            await _until(lambda: hub.syncs >= 1)
            await asyncio.sleep(POLL * 6)  # ещё несколько циклов: повторов нет
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 1
    assert _expiry_calls(panel, ids.server) == [billing.expiry_to_ms(target)]
    assert bool(probes) == bool(health_seconds)
    stored = await _fresh(session, PaymentRequest, payment_id)
    assert stored.status == PaymentStatus.APPLIED and stored.last_error is None
    client = await _fresh(session, VpnClient, ids.client)
    assert billing._as_aware(client.expires_at) == target
    assert await _audit_count(session, "pending_server_update.applied") == 1


async def test_panel_still_down_does_not_sync_subhub(session, ids, wire):  # noqa: F811
    await _pay_during_outage(session, ids.user, ids.server)
    panel = MockPanelUpdater(fail_server_ids={ids.server})
    wire(panel)
    async with LocalSubHub() as hub:
        settings = _settings(subhub_url=hub.url, subhub_admin_token="admin-secret")
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _until(lambda: len(panel.calls) >= 1)
            await asyncio.sleep(POLL * 4)
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 0
    [row] = await _pending(session)
    assert row.status == "pending" and row.attempts == 1


# --- Backoff и повторные ошибки -----------------------------------------------------------------


async def test_worker_respects_next_retry_at(session, ids, wire):  # noqa: F811
    await _pay_during_outage(session, ids.user, ids.server)
    [row] = await _pending(session)
    row.next_retry_at = datetime.now(UTC) + timedelta(hours=1)
    await session.commit()
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await asyncio.sleep(POLL * 8)
        assert panel.calls == []  # backoff не истёк — к панели не обращались
        [row] = await _pending(session)
        row.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()
        await _wait_pending_status(session, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert len(panel.calls) == 1


async def test_repeated_panel_failures_back_off_and_recover(session, ids, wire):  # noqa: F811
    _, target = await _pay_during_outage(session, ids.user, ids.server)
    panel = MockPanelUpdater(fail_server_ids={ids.server})
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        for attempt, delay in ((1, 60), (2, 120), (3, 240)):
            await _until(lambda n=attempt: len(panel.calls) >= n)
            await asyncio.sleep(POLL * 4)
            assert len(panel.calls) == attempt  # следующий повтор — после backoff
            [row] = await _pending(session)
            assert row.status == "pending" and row.attempts == attempt
            remaining = billing._as_aware(row.next_retry_at) - datetime.now(UTC)
            assert timedelta(seconds=delay - 5) < remaining <= timedelta(seconds=delay)
            row.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)  # «время прошло»
            await session.commit()
        panel.fail_server_ids.clear()
        await _wait_pending_status(session, "applied")
        assert not any(task.done() for task in tasks)
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, ids.server)[-1] == billing.expiry_to_ms(target)


async def test_unexpected_error_defers_one_update_and_others_proceed(
    monkeypatch, session, ids, wire  # noqa: F811
):
    await _pay_during_outage(session, ids.user, ids.server, "PAY-1")
    other_user, other_client = await _second_user(session, ids.server)
    await _pay_during_outage(session, other_user, ids.server, "PAY-2")
    original = pending_updates._apply_to_server

    async def poisoned(session_, client, server_, expiry, updater):
        if client.id == ids.client:
            raise RuntimeError("unexpected")
        return await original(session_, client, server_, expiry, updater)

    monkeypatch.setattr(pending_updates, "_apply_to_server", poisoned)
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        async with asyncio.timeout(5):
            while True:
                rows = {row.vpn_client_id: row for row in await _pending(session)}
                if rows[other_client].status == "applied" and rows[ids.client].attempts:
                    break
                await asyncio.sleep(0.01)
        await asyncio.sleep(POLL * 4)
    finally:
        await app_main.stop_background_tasks(tasks)
    rows = {row.vpn_client_id: row for row in await _pending(session)}
    poisoned_row = rows[ids.client]
    assert poisoned_row.status == "pending" and poisoned_row.attempts == 1
    assert poisoned_row.last_error == "RuntimeError: unexpected"
    assert billing._as_aware(poisoned_row.next_retry_at) > datetime.now(UTC)
    assert rows[other_client].status == "applied"


async def test_worker_survives_cycle_failures(monkeypatch, wire):
    attempts: list[int] = []

    async def flaky(_session, _updater, **_kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("database is locked")
        return renewal_recovery.RecoveryReport()

    wire(MockPanelUpdater())
    monkeypatch.setattr(renewal_recovery, "run_once", flaky)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _until(lambda: len(attempts) >= 4)
        assert not any(task.done() for task in tasks)
    finally:
        await app_main.stop_background_tasks(tasks)


async def test_failed_payment_recovery_does_not_block_pending_queue(
    monkeypatch, session, ids, wire  # noqa: F811
):
    await _pay_during_outage(session, ids.user, ids.server)

    async def broken(*_args, **_kwargs):
        raise RuntimeError("payments table locked")

    monkeypatch.setattr(billing, "recover_confirmed_payments", broken)
    wire(MockPanelUpdater())
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_pending_status(session, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)


# --- Прерванное подтверждение (CONFIRMED) после рестарта -----------------------------------------


async def _crash_during_confirmation(
    db, user_id: int, code: str = "PAY-1"
) -> tuple[int, datetime]:
    payment_id = await _waiting_payment(db, user_id, code)
    with pytest.raises(_Crash):
        await billing.confirm_payment(db, payment_id, None, _CrashingPanel())
    await db.rollback()
    stored = await _fresh(db, PaymentRequest, payment_id)
    assert stored.status == PaymentStatus.CONFIRMED and stored.target_expires_at is not None
    # Прошло больше пяти минут: подтверждение считается прерванным, а не текущим.
    stored.confirmed_at = datetime.now(UTC) - timedelta(minutes=10)
    await db.commit()
    return payment_id, billing._as_aware(stored.target_expires_at)


@pytest.mark.parametrize("health_seconds", [0, 60])
async def test_confirmed_payment_resumes_after_restart(
    session, ids, wire, health_seconds  # noqa: F811
):
    payment_id, target = await _crash_during_confirmation(session, ids.user)
    panel = MockPanelUpdater()
    wire(panel)
    async with LocalSubHub() as hub:
        settings = _settings(
            server_health_poll_seconds=health_seconds, subhub_url=hub.url,
            subhub_admin_token="admin-secret", subhub_timeout_seconds=2,
        )
        # Новый процесс: свежий worker без состояния в памяти.
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _wait_payment(session, payment_id, PaymentStatus.APPLIED)
            await _until(lambda: hub.syncs >= 1)
            await asyncio.sleep(POLL * 6)
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 1
    client = await _fresh(session, VpnClient, ids.client)
    assert billing._as_aware(client.expires_at) == target  # срок — сохранённый target
    assert _expiry_calls(panel, ids.server) == [billing.expiry_to_ms(target)]
    assert await _audit_count(session, "billing.applied") == 1


async def test_confirmed_payment_resumed_while_panel_down_then_applied(
    session, ids, wire  # noqa: F811
):
    payment_id, target = await _crash_during_confirmation(session, ids.user)
    panel = MockPanelUpdater(fail_server_ids={ids.server})
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        stored = await _wait_payment(session, payment_id, PaymentStatus.APPLIED)
        assert stored.last_error and "Отложено" in stored.last_error
        await _until(lambda: len(panel.calls) >= 2)  # подтверждение + первый повтор
        [row] = await _pending(session)
        assert row.payment_request_id == payment_id
        row.next_retry_at = None
        panel.fail_server_ids.clear()
        await session.commit()
        await _wait_pending_status(session, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    stored = await _fresh(session, PaymentRequest, payment_id)
    assert stored.last_error is None
    assert _expiry_calls(panel, ids.server)[-1] == billing.expiry_to_ms(target)
    assert await _audit_count(session, "billing.applied") == 1


async def test_failing_confirmed_payment_backs_off_and_does_not_block_others(
    monkeypatch, session, ids  # noqa: F811
):
    """Непредвиденная ошибка повтора откладывает заявку, остальные возобновляются."""
    poisoned, _ = await _crash_during_confirmation(session, ids.user, "PAY-1")
    other_user, _ = await _second_user(session, ids.server)
    healthy, _ = await _crash_during_confirmation(session, other_user, "PAY-2")
    original = billing.retry_payment
    calls: list[int] = []

    async def flaky_retry(session_, payment_id, actor, updater, now=None):
        calls.append(payment_id)
        if payment_id == poisoned:
            raise RuntimeError("unexpected")
        return await original(session_, payment_id, actor, updater, now)

    monkeypatch.setattr(billing, "retry_payment", flaky_retry)
    backoff = pending_updates.RetryBackoff()
    panel = MockPanelUpdater()
    first = await renewal_recovery.run_once(session, panel, backoff=backoff)
    assert first.payments_recovered == 1
    second = await renewal_recovery.run_once(session, panel, backoff=backoff)
    assert second.payments_recovered == 0
    assert calls == [poisoned, healthy]  # во втором проходе — backoff, без обращений
    assert backoff.attempts == {poisoned: 1}
    stored = await _fresh(session, PaymentRequest, poisoned)
    assert stored.status == PaymentStatus.CONFIRMED  # заявка не потеряна
    # Backoff истёк, ошибка ушла — заявка применяется и снимается с backoff.
    backoff.next_at[poisoned] = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(billing, "retry_payment", original)
    third = await renewal_recovery.run_once(session, panel, backoff=backoff)
    assert third.payments_recovered == 1 and backoff.attempts == {}


# --- Идемпотентность и более новый оплаченный срок -------------------------------------------


async def test_concurrent_handlers_apply_each_update_once(session, ids):  # noqa: F811
    """Два обработчика (например, два процесса) над одной очередью: одно применение."""
    await _pay_during_outage(session, ids.user, ids.server)
    panel = MockPanelUpdater()
    maker = _maker(session)
    async with maker() as first, maker() as second:
        results = await asyncio.gather(
            pending_updates.process_due(first, panel),
            pending_updates.process_due(second, panel),
        )
    flat = [item for batch in results for item in batch]
    assert sum(1 for item in flat if item.ok and not item.already_done) == 1
    assert len(panel.calls) == 1
    assert await _audit_count(session, "pending_server_update.applied") == 1
    # Повторный проход ничего не делает.
    assert await pending_updates.process_due(session, panel) == []
    assert len(panel.calls) == 1


async def test_delayed_update_keeps_newer_paid_expiry(session, ids, wire):  # noqa: F811
    _, first_target = await _pay_during_outage(session, ids.user, ids.server, "PAY-1")
    # Панель вернулась, пользователь оплатил ещё раз раньше, чем сработала очередь.
    second = await _waiting_payment(session, ids.user, "PAY-2")
    result = await billing.confirm_payment(session, second, None, MockPanelUpdater())
    newer = billing._as_aware(result.new_expires_at)
    assert newer > first_target
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_pending_status(session, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, ids.server) == [billing.expiry_to_ms(newer)]
    client = await _fresh(session, VpnClient, ids.client)
    assert billing._as_aware(client.expires_at) == newer


# --- Отключённые и удалённые серверы -----------------------------------------------------------


async def test_disabled_server_waits_until_enabled(session, ids, wire):  # noqa: F811
    _, target = await _pay_during_outage(session, ids.user, ids.server)
    (await _fresh(session, Server, ids.server)).enabled = False
    await session.commit()
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await asyncio.sleep(POLL * 8)
        assert panel.calls == []
        [row] = await _pending(session)
        assert row.status == "pending" and row.attempts == 0  # backoff не тратится
        (await _fresh(session, Server, ids.server)).enabled = True
        await session.commit()
        await _wait_pending_status(session, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, ids.server) == [billing.expiry_to_ms(target)]


async def test_deleted_server_rows_are_closed_by_worker(session, ids, wire):  # noqa: F811
    """Строки удалённого сервера, оставшиеся без каскада, закрываются, заявка — без ошибки."""
    payment_id, _ = await _pay_during_outage(session, ids.user, ids.server)
    assert await ServerRepository(session).delete(ids.server)
    await session.commit()
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_pending_status(session, "failed")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert panel.calls == []
    stored = await _fresh(session, PaymentRequest, payment_id)
    assert stored.status == PaymentStatus.APPLIED and stored.last_error is None


async def test_admin_server_deletion_closes_pending_updates(session, ids):  # noqa: F811
    payment_id, _ = await _pay_during_outage(session, ids.user, ids.server)
    assert await pending_updates.close_for_server(session, ids.server, "server deleted") == 1
    await ServerRepository(session).delete(ids.server)
    await session.commit()
    [row] = await _pending(session)
    assert row.status == "failed" and row.last_error == "server deleted"
    stored = await _fresh(session, PaymentRequest, payment_id)
    assert stored.last_error is None
    assert await pending_updates.process_due(session, MockPanelUpdater()) == []


# --- Завершение приложения -----------------------------------------------------------------------


async def test_stop_cancels_worker_blocked_on_panel_and_restart_applies(
    session, ids, wire  # noqa: F811
):
    _, target = await _pay_during_outage(session, ids.user, ids.server)
    hanging = _HangingPanel()
    wire(hanging)
    tasks = app_main.start_background_tasks(object(), _settings())
    await asyncio.wait_for(hanging.entered.wait(), 2)
    await asyncio.wait_for(app_main.stop_background_tasks(tasks), 2)
    assert hanging.cancelled.is_set() and all(task.done() for task in tasks)
    [row] = await _pending(session)
    assert row.status == "pending" and row.attempts == 0  # отмена не испортила запись

    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_pending_status(session, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, ids.server) == [billing.expiry_to_ms(target)]


def test_retry_delay_schedule():
    """Ошибки панели и непредвиденные ошибки используют один backoff: 1 мин → 1 ч."""
    assert [pending_updates.retry_delay(n).total_seconds() for n in (1, 2, 7, 20)] == [
        60, 120, 3600, 3600,
    ]
