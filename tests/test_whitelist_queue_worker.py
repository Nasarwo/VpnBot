"""Очередь применения whitelist-квот не зависит от проверки здоровья серверов.

Дефект: автоматический ``whitelist.process_due`` находился внутри
``_server_health_poller`` и при ``SERVER_HEALTH_POLL_SECONDS=0`` не запускался —
покупка, сохранённая при недоступной панели, после её восстановления сама не
применялась. Теперь очередь обслуживает отдельный worker ``_whitelist_queue_worker``.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import main as app_main
from app.config import Settings
from app.db.base import Base
from app.db.models import VpnClient, WhitelistAccount
from app.services import billing, whitelist
from app.services.panel_updater import MockPanelUpdater
from tests.test_subhub_trigger import LocalSubHub
from tests.test_whitelist import (  # noqa: F401
    EMAIL,
    _account,
    _buy,
    _ledger_count,
    _pay,
    service_on,
    wl_server,
)
from tests.test_whitelist_reconcile import START_FREE, _add_account, _email

GIB = whitelist.GIB
QUEUE_POLL = 0.02  # секунды: быстрый цикл worker'а в тестах


def _settings(**overrides) -> Settings:
    base: dict[str, Any] = {
        "anti_sharing_enabled": False,
        "expiry_notify_poll_seconds": 0,
        "server_health_poll_seconds": 0,
        "whitelist_reconcile_minutes": 0,
        "whitelist_queue_poll_seconds": QUEUE_POLL,
    }
    base.update(overrides)
    return Settings(**base)


@pytest_asyncio.fixture
async def session(tmp_path) -> AsyncIterator[AsyncSession]:
    """БД в файле с отдельными соединениями у теста и у фонового worker'а.

    Общее соединение (StaticPool из conftest) не годится: worker работает
    параллельно с тестом, а отмена посреди запроса портит общий курсор.
    """
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'queue.sqlite3'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _wal(dbapi_connection, _record) -> None:
        dbapi_connection.execute("PRAGMA journal_mode=WAL")
        dbapi_connection.execute("PRAGMA busy_timeout=5000")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _maker_for(engine)() as s:
        yield s
    await engine.dispose()


def _maker_for(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


def _maker(session: AsyncSession) -> async_sessionmaker[AsyncSession]:
    return _maker_for(session.bind)


@pytest.fixture
def wire(monkeypatch, session):
    """Подключает фоновые задачи приложения к БД теста и подменяемой панели."""

    def _wire(panel: MockPanelUpdater) -> None:
        monkeypatch.setattr(app_main, "get_sessionmaker", lambda: _maker(session))
        monkeypatch.setattr(app_main, "build_updater", lambda **_: panel)

    return _wire


async def _expire(session, user) -> None:
    """Сбрасывает кэш сессии, чтобы увидеть записи worker'а; пользователь остаётся доступным."""
    session.expire_all()
    await session.refresh(user)


async def _wait_applied(session, user, timeout: float = 5.0) -> None:
    """Ждёт, пока worker зафиксирует применение в БД (на панели оно видно раньше commit)."""
    async with asyncio.timeout(timeout):
        while True:
            await _expire(session, user)
            account = await _account(session, user)
            if account.applied_version == account.desired_version:
                return
            await session.rollback()
            await asyncio.sleep(0.01)


async def _until(predicate, timeout: float = 5.0) -> None:
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


# --- Какие задачи запускаются ------------------------------------------------------------


@pytest.fixture
def started(monkeypatch):
    """Подменяет фоновые циклы метками: видно, какие из них запустил start_background_tasks."""
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


@pytest.mark.parametrize("health", [0, 60])
@pytest.mark.parametrize("reconcile", [0, 15])
async def test_queue_worker_runs_for_every_health_and_reconcile_combination(
    started, health, reconcile
):
    settings = _settings(
        server_health_poll_seconds=health, whitelist_reconcile_minutes=reconcile
    )
    tasks = app_main.start_background_tasks(object(), settings)
    await asyncio.sleep(0)
    try:
        assert started.count("queue") == 1
        assert started.count("health") == (1 if health else 0)
        assert started.count("reconcile") == (1 if reconcile else 0)
    finally:
        await app_main.stop_background_tasks(tasks)


async def test_second_start_in_same_process_does_not_add_second_queue_worker(started):
    settings = _settings(server_health_poll_seconds=60)
    first = app_main.start_background_tasks(object(), settings)
    second = app_main.start_background_tasks(object(), settings)
    await asyncio.sleep(0)
    try:
        assert started.count("queue") == 1
    finally:
        await app_main.stop_background_tasks(first + second)


async def test_queue_worker_can_be_restarted_after_stop(started):
    settings = _settings()
    for expected in (1, 2):
        tasks = app_main.start_background_tasks(object(), settings)
        await asyncio.sleep(0)
        assert started.count("queue") == expected
        await app_main.stop_background_tasks(tasks)
        assert all(task.done() for task in tasks)


async def test_stop_background_tasks_finishes_worker_blocked_on_panel(
    monkeypatch, session, wire
):
    """Завершение не зависает на зависшем запросе панели: задача отменяется."""
    entered = asyncio.Event()
    cancelled = asyncio.Event()

    async def hang(_session, _updater, **_kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    wire(MockPanelUpdater())
    monkeypatch.setattr(whitelist, "process_due", hang)
    tasks = app_main.start_background_tasks(object(), _settings())
    await asyncio.wait_for(entered.wait(), 2)
    await asyncio.wait_for(app_main.stop_background_tasks(tasks), 2)
    assert cancelled.is_set() and all(task.done() for task in tasks)


async def test_health_poller_no_longer_processes_whitelist_queue(monkeypatch, wire):
    """Очередь обслуживает только worker: при включённом health polling обработки нет дважды."""
    from app.services import health

    calls: list[str] = []

    async def fake_recover(session, updater):
        return 0

    async def fake_check(session, **kwargs):
        calls.append("check")
        return {}

    async def forbidden(session, updater, **kwargs):
        raise AssertionError("health poller must not process the whitelist queue")

    async def stop_sleep(_seconds):
        raise asyncio.CancelledError

    wire(MockPanelUpdater())
    monkeypatch.setattr(billing, "recover_confirmed_payments", fake_recover)
    monkeypatch.setattr(health, "check_servers", fake_check)
    monkeypatch.setattr(whitelist, "process_due", forbidden)
    monkeypatch.setattr(app_main.asyncio, "sleep", stop_sleep)
    with pytest.raises(asyncio.CancelledError):
        await app_main._server_health_poller(_settings(server_health_poll_seconds=60))
    assert calls == ["check"]


# --- Сквозной сценарий: панель недоступна → восстановление → применение ---------------------


async def _purchase_while_panel_down(session, user, panel, server):
    await _pay(session, user, panel)
    panel.fail_server_ids.add(server.id)
    payment, result = await _buy(session, user, panel, 25)
    assert result.applied and result.whitelist_pending
    account = await _account(session, user)
    assert account.desired_version > account.applied_version
    return payment, account


@pytest.mark.parametrize("health", [0, 60])
async def test_purchase_during_panel_outage_is_applied_after_recovery_without_admin(
    session, user, vpn_client, service_on, wl_server, wire, health  # noqa: F811
):
    panel = MockPanelUpdater()
    wire(panel)
    await _purchase_while_panel_down(session, user, panel, wl_server)
    state = panel.quota_clients[(wl_server.id, EMAIL)]
    assert state.total_bytes == START_FREE  # панель ещё не получила начисление
    # Панель восстановилась; очередь не должна ждать административной команды.
    panel.fail_server_ids.clear()
    account = await _account(session, user)
    account.next_sync_at = None
    await session.commit()

    async with LocalSubHub() as hub:
        settings = _settings(
            server_health_poll_seconds=health,
            subhub_url=hub.url,
            subhub_admin_token="admin-secret",
            subhub_timeout_seconds=2,
        )
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _until(lambda: state.total_bytes == START_FREE + 25 * GIB)
            await _until(lambda: hub.syncs >= 1)
            await asyncio.sleep(QUEUE_POLL * 5)  # ещё несколько циклов: повторов нет
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 1  # уведомление SubHub после успешного применения — один раз

    await _expire(session, user)
    account = await _account(session, user)
    assert account.applied_version == account.desired_version
    assert account.paid_bytes == 25 * GIB  # начислено один раз
    assert await _ledger_count(session, user.id, "purchase") == 1
    assert state.total_bytes == START_FREE + 25 * GIB


async def test_queue_worker_respects_backoff_until_it_expires(
    session, user, vpn_client, service_on, wl_server, wire  # noqa: F811
):
    panel = MockPanelUpdater()
    wire(panel)
    await _purchase_while_panel_down(session, user, panel, wl_server)
    panel.fail_server_ids.clear()
    account = await _account(session, user)
    account.next_sync_at = datetime.now(UTC) + timedelta(hours=1)
    await session.commit()
    state = panel.quota_clients[(wl_server.id, EMAIL)]
    writes_before = len(panel.quota_applied)

    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await asyncio.sleep(QUEUE_POLL * 6)
        assert state.total_bytes == START_FREE  # backoff ещё не истёк
        assert len(panel.quota_applied) == writes_before  # к панели не обращались
        account = await _account(session, user)
        account.next_sync_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()
        await _until(lambda: state.total_bytes == START_FREE + 25 * GIB)
    finally:
        await app_main.stop_background_tasks(tasks)


async def test_worker_survives_cycle_failure_and_keeps_polling(monkeypatch, wire):
    attempts: list[int] = []

    async def flaky(_session, _updater, **_kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise RuntimeError("database is locked")
        return 0

    wire(MockPanelUpdater())
    monkeypatch.setattr(whitelist, "process_due", flaky)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _until(lambda: len(attempts) >= 4)
        assert not any(task.done() for task in tasks)
    finally:
        await app_main.stop_background_tasks(tasks)


async def test_subhub_failure_does_not_block_or_repeat_application(
    session, user, vpn_client, service_on, wl_server, wire  # noqa: F811
):
    """Недоступный SubHub не откатывает применение и не создаёт повторов."""
    panel = MockPanelUpdater()
    wire(panel)
    await _purchase_while_panel_down(session, user, panel, wl_server)
    panel.fail_server_ids.clear()
    account = await _account(session, user)
    account.next_sync_at = None
    await session.commit()
    state = panel.quota_clients[(wl_server.id, EMAIL)]
    async with LocalSubHub("drop") as hub:
        settings = _settings(
            subhub_url=hub.url, subhub_admin_token="admin-secret", subhub_timeout_seconds=2
        )
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _until(lambda: state.total_bytes == START_FREE + 25 * GIB)
            await _until(lambda: hub.syncs >= 1)
            await asyncio.sleep(QUEUE_POLL * 5)
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 1
    await _expire(session, user)
    assert await _ledger_count(session, user.id, "purchase") == 1


# --- Ошибка одного аккаунта, остальные продолжают обрабатываться ----------------------------


class _PoisonedPanel(MockPanelUpdater):
    """Панель, на которой запись одного клиента падает непредвиденной ошибкой."""

    def __init__(self, poisoned_email: str) -> None:
        super().__init__()
        self.poisoned_email = poisoned_email
        self.poisoned_attempts = 0

    async def apply_quota_client(self, server, spec, target):
        if spec.email == self.poisoned_email:
            self.poisoned_attempts += 1
            raise RuntimeError("unexpected failure")
        return await super().apply_quota_client(server, spec, target)


async def test_one_failing_account_does_not_stop_the_rest_of_the_queue(
    session, wl_server, wire  # noqa: F811
):
    panel = _PoisonedPanel(_email(0))
    wire(panel)
    ids = []
    for index in range(4):
        account = await _add_account(session, wl_server, panel, index)
        account.desired_version = 2  # применённая версия 1 — запись ждёт очереди
        session.add(
            VpnClient(
                user_id=account.user_id, display_name=f"U{index}", email=_email(index),
                expires_at=datetime.now(UTC) + timedelta(days=30), is_active=True,
                subscription_url_direct=f"https://sub.example/{index}",
            )
        )
        ids.append(account.id)
    await session.commit()

    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _until(lambda: len(panel.quota_applied) >= 3 and panel.poisoned_attempts >= 2)
        await asyncio.sleep(QUEUE_POLL * 4)
    finally:
        await app_main.stop_background_tasks(tasks)

    session.expire_all()
    versions = {
        a.panel_email: (a.applied_version, a.desired_version)
        for a in (await session.scalars(select(WhitelistAccount))).all()
    }
    assert versions[_email(0)] == (1, 2)  # сбойный остаётся в очереди и повторяется
    assert all(versions[_email(i)] == (2, 2) for i in (1, 2, 3))  # остальные применены


# --- Перезапуск worker'а и сохранённое состояние ---------------------------------------------


async def test_restarted_worker_applies_pending_purchase_exactly_once(
    session, user, vpn_client, service_on, wl_server, wire  # noqa: F811
):
    panel = MockPanelUpdater()
    wire(panel)
    await _purchase_while_panel_down(session, user, panel, wl_server)
    state = panel.quota_clients[(wl_server.id, EMAIL)]

    # Первый worker работает, пока панель недоступна: применение откладывается.
    tasks = app_main.start_background_tasks(object(), _settings())
    await asyncio.sleep(QUEUE_POLL * 4)
    await app_main.stop_background_tasks(tasks)
    assert state.total_bytes == START_FREE

    # Процесс «перезапущен», панель вернулась — новый worker берёт запись из БД.
    panel.fail_server_ids.clear()
    account = await _account(session, user)
    account.next_sync_at = None
    await session.commit()
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _until(lambda: state.total_bytes == START_FREE + 25 * GIB)
        await _wait_applied(session, user)
        await asyncio.sleep(QUEUE_POLL * 4)
    finally:
        await app_main.stop_background_tasks(tasks)
    await _expire(session, user)
    assert await _ledger_count(session, user.id, "purchase") == 1
    assert (await _account(session, user)).paid_bytes == 25 * GIB


async def test_expired_subscription_keeps_paid_traffic_when_queue_applies_it(
    session, user, vpn_client, service_on, wl_server, wire  # noqa: F811
):
    panel = MockPanelUpdater()
    wire(panel)
    await _purchase_while_panel_down(session, user, panel, wl_server)
    # Пока панель была недоступна, подписка истекла.
    vpn_client.expires_at = datetime.now(UTC) - timedelta(days=1)
    vpn_client.is_active = False
    panel.fail_server_ids.clear()
    account = await _account(session, user)
    account.next_sync_at = None
    await session.commit()
    state = panel.quota_clients[(wl_server.id, EMAIL)]

    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _until(lambda: state.total_bytes == START_FREE + 25 * GIB)
        await _wait_applied(session, user)
    finally:
        await app_main.stop_background_tasks(tasks)

    await _expire(session, user)
    account = await _account(session, user)
    assert account.paid_bytes == 25 * GIB  # платный трафик не потерян
    assert not state.enable  # доступ закрыт сроком подписки
    assert state.expiry_ms and state.expiry_ms < int(datetime.now(UTC).timestamp() * 1000)
    assert await _ledger_count(session, user.id, "purchase") == 1

    # Продление возвращает доступ без повторного начисления.
    vpn_client.expires_at = datetime.now(UTC) + timedelta(days=30)
    vpn_client.is_active = True
    await session.commit()
    await whitelist.sync_user(session, user.id, panel)
    assert panel.quota_clients[(wl_server.id, EMAIL)].enable
    assert await _ledger_count(session, user.id, "purchase") == 1

