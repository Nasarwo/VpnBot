"""Worker восстановления обычных продлений на PostgreSQL.

Запуск: VPNBOT_TEST_PG_URL=postgresql+asyncpg://user@host:port/db pytest
База должна быть отдельной тестовой: схема пересоздаётся каждым тестом.

In-process asyncio.Lock подменяется (``_NoLocalLocks``): каждый обработчик ведёт
себя как отдельный процесс и сериализуется только advisory lock
(``pg_advisory_lock(176884, user_id)``) и блокировками строк PostgreSQL. Порядок
операций задаётся явно: тестовая панель останавливает обработчик внутри
блокировки на событии, а ожидание конкурента на advisory lock определяется по
``pg_locks`` (``granted = false``). Панели — ``MockPanelUpdater``, SubHub —
локальный HTTP-сервер.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import main as app_main
from app.db.base import Base
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
from app.services import billing, health, operation_lock, pending_updates, renewal_recovery
from app.services.panel_updater import MockPanelUpdater
from tests.test_renewal_recovery_worker import (
    _Crash,
    _CrashingPanel,
    _HangingPanel,
    _settings,
    _waiting_payment,
)
from tests.test_subhub_trigger import LocalSubHub
from tests.test_whitelist_pg import PG_URL, _NoLocalLocks

pytestmark = pytest.mark.skipif(not PG_URL, reason="VPNBOT_TEST_PG_URL is not set")

LOCK_CLASS = 176884  # первый ключ advisory lock пользователя (operation_lock)
DAY = timedelta(days=1)


@dataclass(frozen=True, slots=True)
class Env:
    maker: async_sessionmaker
    engine: object
    user: int
    client: int
    server: int
    expires: datetime


@pytest_asyncio.fixture
async def env(monkeypatch):
    monkeypatch.setattr(operation_lock, "_locks", _NoLocalLocks())
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        user = User(telegram_id=4242, username="u", first_name="U", role=UserRole.USER,
                    onboarding_done=True, public_id="PUBREC")
        server = Server(name="std", panel_url="https://std", username="a", password="b",
                        enabled=True)
        session.add_all([user, server])
        await session.flush()
        client = VpnClient(user_id=user.id, display_name="c", email="PUBREC",
                           is_active=True,
                           expires_at=datetime.now(UTC).replace(microsecond=0) + 10 * DAY)
        session.add(client)
        await session.flush()
        session.add(ClientServerMapping(
            vpn_client_id=client.id, server_id=server.id, inbound_id=1,
            protocol=Protocol.VLESS, client_uuid="uuid-rec", email="PUBREC", enabled=True,
        ))
        await session.commit()
        result = Env(maker=maker, engine=engine, user=user.id, client=client.id,
                     server=server.id, expires=billing._as_aware(client.expires_at))
    yield result
    await engine.dispose()


@pytest.fixture
def wire(monkeypatch, env):
    """Фоновые задачи приложения — на тестовой PostgreSQL и подменённой панели."""

    async def no_network(server, timeout: float = 10.0) -> bool:  # noqa: ARG001
        return True

    def _wire(panel: MockPanelUpdater) -> None:
        monkeypatch.setattr(app_main, "get_sessionmaker", lambda: env.maker)
        monkeypatch.setattr(
            "app.services.whitelist_labels.get_sessionmaker", lambda: env.maker
        )
        monkeypatch.setattr(app_main, "build_updater", lambda **_: panel)
        monkeypatch.setattr(health, "check_server", no_network)

    return _wire


@pytest.fixture
def cycles(monkeypatch):
    """Счётчик завершённых проходов worker'а — явная точка синхронизации."""
    done: list[renewal_recovery.RecoveryReport] = []
    original = renewal_recovery.run_once

    async def counted(session, updater, *, backoff):
        report = await original(session, updater, backoff=backoff)
        done.append(report)
        return report

    monkeypatch.setattr(renewal_recovery, "run_once", counted)
    return done


class GatedPanel(MockPanelUpdater):
    """Останавливает обращения к панели, пока тест не откроет ``release``."""

    def __init__(self, fail_server_ids: set[int] | None = None) -> None:
        super().__init__(fail_server_ids)
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def update_expiry(self, server, mapping, expiry_ms):
        self.entered.set()
        await self.release.wait()
        await super().update_expiry(server, mapping, expiry_ms)


# --- Наблюдение за PostgreSQL из независимого соединения ---------------------------------------


async def _advisory(env: Env) -> tuple[int, int]:
    """(удерживаемые, ожидающие) advisory lock'и пользователя по ``pg_locks``."""
    async with env.engine.connect() as conn:
        rows = (await conn.execute(text(
            "SELECT granted, count(*) FROM pg_locks WHERE locktype = 'advisory' "
            "AND classid::bigint = :cls AND objid::bigint = :owner AND objsubid = 2 "
            "GROUP BY granted"
        ), {"cls": LOCK_CLASS, "owner": env.user})).all()
    counts = {bool(granted): count for granted, count in rows}
    return counts.get(True, 0), counts.get(False, 0)


async def _wait_lock_waiters(env: Env, count: int = 1) -> None:
    """Ждёт, пока ``count`` обработчиков встанут в очередь на advisory lock."""
    async with asyncio.timeout(5):
        while (await _advisory(env))[1] < count:
            await asyncio.sleep(0.01)


async def _uncommitted_writers(env: Env) -> int:
    """Клиентские соединения с незафиксированной записью (назначен xid)."""
    async with env.engine.connect() as conn:
        return await conn.scalar(text(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
            "AND backend_type = 'client backend' AND backend_xid IS NOT NULL "
            "AND pid <> pg_backend_pid()"
        ))


async def _idle_in_transaction(env: Env) -> int:
    async with env.engine.connect() as conn:
        return await conn.scalar(text(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
            "AND state LIKE 'idle in transaction%' AND pid <> pg_backend_pid()"
        ))


# --- Данные ---------------------------------------------------------------------------------


async def _pay_during_outage(env: Env, code: str = "PAY-1") -> tuple[int, datetime]:
    """Оплата подтверждена при недоступной панели: APPLIED + отложенное обновление."""
    async with env.maker() as session:
        payment_id = await _waiting_payment(session, env.user, code)
        down = MockPanelUpdater(fail_server_ids={env.server})
        result = await billing.confirm_payment(session, payment_id, None, down)
    assert result.applied and [r.server_id for r in result.failed_servers] == [env.server]
    return payment_id, billing._as_aware(result.new_expires_at)


async def _crash_during_confirmation(env: Env, code: str = "PAY-1") -> tuple[int, datetime]:
    """Процесс упал после фиксации target: заявка CONFIRMED старше пяти минут."""
    async with env.maker() as session:
        payment_id = await _waiting_payment(session, env.user, code)
        with pytest.raises(_Crash):
            await billing.confirm_payment(session, payment_id, None, _CrashingPanel())
        await session.rollback()
        stored = await session.get(PaymentRequest, payment_id, populate_existing=True)
        assert stored.status == PaymentStatus.CONFIRMED and stored.target_expires_at
        stored.confirmed_at = datetime.now(UTC) - timedelta(minutes=10)
        await session.commit()
        return payment_id, billing._as_aware(stored.target_expires_at)


async def _confirm(env: Env, payment_id: int, panel) -> billing.BillingResult:
    async with env.maker() as session:
        return await billing.confirm_payment(session, payment_id, None, panel)


async def _run_once(env: Env, panel) -> renewal_recovery.RecoveryReport:
    async with env.maker() as session:
        return await renewal_recovery.run_once(
            session, panel, backoff=pending_updates.RetryBackoff()
        )


async def _rows(env: Env) -> list[PendingServerUpdate]:
    async with env.maker() as session:
        return list((await session.scalars(
            select(PendingServerUpdate).order_by(PendingServerUpdate.id)
        )).all())


async def _payment(env: Env, payment_id: int) -> PaymentRequest:
    async with env.maker() as session:
        return await session.get(PaymentRequest, payment_id)


async def _client_expiry(env: Env) -> datetime:
    async with env.maker() as session:
        return billing._as_aware((await session.get(VpnClient, env.client)).expires_at)


async def _audit(env: Env, action: str) -> int:
    async with env.maker() as session:
        return await session.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == action)
        )


async def _set_retry_at(env: Env, when: datetime | None) -> None:
    async with env.maker() as session:
        await session.execute(update(PendingServerUpdate).values(next_retry_at=when))
        await session.commit()


async def _wait_rows(env: Env, status: str) -> None:
    async with asyncio.timeout(5):
        while True:
            rows = await _rows(env)
            if rows and all(row.status == status for row in rows):
                return
            await asyncio.sleep(0.01)


async def _wait_payment(env: Env, payment_id: int, status: PaymentStatus) -> None:
    async with asyncio.timeout(5):
        while (await _payment(env, payment_id)).status != status:
            await asyncio.sleep(0.01)


async def _wait_cycles(done: list, count: int) -> None:
    start = len(done)
    async with asyncio.timeout(5):
        while len(done) < start + count:
            await asyncio.sleep(0.01)


def _ms(value: datetime) -> int:
    return billing.expiry_to_ms(value)


def _expiry_calls(panel: MockPanelUpdater, server_id: int) -> list[int]:
    return [ms for sid, ms in panel.calls if sid == server_id]


# --- Восстановление без проверки здоровья серверов ----------------------------------------------


@pytest.mark.parametrize("health_seconds", [0, 60])
async def test_payment_during_outage_reaches_panel_without_health_polling(
    env, wire, cycles, health_seconds
):
    payment_id, target = await _pay_during_outage(env)
    panel = MockPanelUpdater()
    wire(panel)
    async with LocalSubHub() as hub:
        settings = _settings(
            server_health_poll_seconds=health_seconds, subhub_url=hub.url,
            subhub_admin_token="admin-secret", subhub_timeout_seconds=2,
        )
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _wait_rows(env, "applied")
            await _wait_cycles(cycles, 4)  # ещё несколько проходов: повторов нет
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 1
    assert _expiry_calls(panel, env.server) == [_ms(target)]
    stored = await _payment(env, payment_id)
    assert stored.status == PaymentStatus.APPLIED and stored.last_error is None
    assert await _client_expiry(env) == target
    assert await _audit(env, "pending_server_update.applied") == 1
    assert await _advisory(env) == (0, 0)


@pytest.mark.parametrize("health_seconds", [0, 60])
async def test_confirmed_payment_resumes_after_restart(env, wire, cycles, health_seconds):
    payment_id, target = await _crash_during_confirmation(env)
    panel = MockPanelUpdater()
    wire(panel)
    async with LocalSubHub() as hub:
        settings = _settings(
            server_health_poll_seconds=health_seconds, subhub_url=hub.url,
            subhub_admin_token="admin-secret", subhub_timeout_seconds=2,
        )
        tasks = app_main.start_background_tasks(object(), settings)
        try:
            await _wait_payment(env, payment_id, PaymentStatus.APPLIED)
            await _wait_cycles(cycles, 4)
        finally:
            await app_main.stop_background_tasks(tasks)
        assert hub.syncs == 1
    assert await _client_expiry(env) == target
    assert _expiry_calls(panel, env.server) == [_ms(target)]
    assert await _audit(env, "billing.applied") == 1


# --- Два независимых обработчика ---------------------------------------------------------------


async def test_two_handlers_apply_one_pending_update_once(env):
    _, target = await _pay_during_outage(env)
    panel = GatedPanel()
    first = asyncio.create_task(_run_once(env, panel))
    await asyncio.wait_for(panel.entered.wait(), 5)  # первый держит блокировку у панели
    assert await _advisory(env) == (1, 0)
    second = asyncio.create_task(_run_once(env, panel))
    await _wait_lock_waiters(env)  # второй выбрал ту же запись и ждёт блокировку
    assert not second.done()
    panel.release.set()
    reports = await asyncio.gather(first, second)

    assert sorted(r.updates_applied for r in reports) == [0, 1]
    assert [r.changed for r in reports].count(True) == 1  # SubHub sync — один раз
    assert _expiry_calls(panel, env.server) == [_ms(target)]
    [row] = await _rows(env)
    assert (row.status, row.attempts, row.next_retry_at) == ("applied", 1, None)
    assert await _audit(env, "pending_server_update.applied") == 1
    assert await _advisory(env) == (0, 0)


async def test_two_handlers_resume_one_confirmed_payment_once(env):
    payment_id, target = await _crash_during_confirmation(env)
    panel = GatedPanel()
    first = asyncio.create_task(_run_once(env, panel))
    await asyncio.wait_for(panel.entered.wait(), 5)
    second = asyncio.create_task(_run_once(env, panel))
    await _wait_lock_waiters(env)
    assert not second.done()
    panel.release.set()
    reports = await asyncio.gather(first, second)

    assert sorted(r.payments_recovered for r in reports) == [0, 1]
    assert _expiry_calls(panel, env.server) == [_ms(target)]
    assert (await _payment(env, payment_id)).status == PaymentStatus.APPLIED
    assert await _client_expiry(env) == target
    assert await _audit(env, "billing.applied") == 1


# --- Конкуренция восстановления со свежей оплатой ---------------------------------------------


@pytest.mark.parametrize("first", ["recovery", "payment"])
async def test_pending_update_racing_fresh_payment_never_shortens_expiry(env, first):
    _, older = await _pay_during_outage(env, "PAY-1")
    async with env.maker() as session:
        fresh = await _waiting_payment(session, env.user, "PAY-2")
    panel = GatedPanel()
    if first == "recovery":
        recovery = asyncio.create_task(_run_once(env, panel))
        await asyncio.wait_for(panel.entered.wait(), 5)
        payment = asyncio.create_task(_confirm(env, fresh, panel))
    else:
        payment = asyncio.create_task(_confirm(env, fresh, panel))
        await asyncio.wait_for(panel.entered.wait(), 5)
        recovery = asyncio.create_task(_run_once(env, panel))
    await _wait_lock_waiters(env)
    panel.release.set()
    report, result = await asyncio.gather(recovery, payment)

    newer = older + 30 * DAY
    assert result.applied and billing._as_aware(result.new_expires_at) == newer
    assert report.updates_applied == 1
    calls = _expiry_calls(panel, env.server)
    if first == "recovery":
        assert calls == [_ms(older), _ms(newer)]
    else:
        # Отложенное обновление применено после свежей оплаты — её срок, не свой.
        assert calls == [_ms(newer), _ms(newer)]
    assert await _client_expiry(env) == newer
    [row] = await _rows(env)
    assert row.status == "applied"


@pytest.mark.parametrize("first", ["recovery", "payment"])
async def test_confirmed_recovery_racing_fresh_payment_never_shortens_expiry(env, first):
    interrupted, target = await _crash_during_confirmation(env, "PAY-1")
    async with env.maker() as session:
        fresh = await _waiting_payment(session, env.user, "PAY-2")
    panel = GatedPanel()
    if first == "recovery":
        recovery = asyncio.create_task(_run_once(env, panel))
        await asyncio.wait_for(panel.entered.wait(), 5)
        payment = asyncio.create_task(_confirm(env, fresh, panel))
    else:
        payment = asyncio.create_task(_confirm(env, fresh, panel))
        await asyncio.wait_for(panel.entered.wait(), 5)
        recovery = asyncio.create_task(_run_once(env, panel))
    await _wait_lock_waiters(env)
    panel.release.set()
    report, result = await asyncio.gather(recovery, payment)

    # Обе оплаты по 30 дней учтены, независимо от порядка.
    assert target == env.expires + 30 * DAY
    final = env.expires + 60 * DAY
    assert report.payments_recovered == 1 and result.applied
    assert await _client_expiry(env) == final
    calls = _expiry_calls(panel, env.server)
    assert calls[-1] == _ms(final)
    assert calls == sorted(calls)  # панель ни разу не получила более ранний срок позже
    for payment_id in (interrupted, fresh):
        assert (await _payment(env, payment_id)).status == PaymentStatus.APPLIED
    assert await _audit(env, "billing.applied") == 2


# --- next_retry_at и backoff ------------------------------------------------------------------


async def test_next_retry_at_and_backoff_on_postgresql(env):
    _, target = await _pay_during_outage(env)
    panel = MockPanelUpdater(fail_server_ids={env.server})
    for attempt, delay in ((1, 60), (2, 120), (3, 240)):
        report = await _run_once(env, panel)
        assert (report.updates_applied, report.updates_failed) == (0, 1)
        [row] = await _rows(env)
        assert row.status == "pending" and row.attempts == attempt
        assert row.next_retry_at.tzinfo is not None
        remaining = row.next_retry_at - datetime.now(UTC)
        assert timedelta(seconds=delay - 5) < remaining <= timedelta(seconds=delay)
        # Backoff не истёк: следующий проход к панели не обращается.
        report = await _run_once(env, panel)
        assert (report.updates_applied, report.updates_failed) == (0, 0)
        assert len(panel.calls) == attempt
        await _set_retry_at(env, datetime.now(UTC) - timedelta(seconds=1))
    panel.fail_server_ids.clear()
    report = await _run_once(env, panel)
    assert report.updates_applied == 1 and report.changed
    [row] = await _rows(env)
    assert (row.status, row.attempts, row.next_retry_at, row.last_error) == (
        "applied", 4, None, None,
    )
    assert _expiry_calls(panel, env.server)[-1] == _ms(target)


async def test_worker_waits_for_next_retry_at(env, wire, cycles):
    _, target = await _pay_during_outage(env)
    await _set_retry_at(env, datetime.now(UTC) + timedelta(hours=1))
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_cycles(cycles, 5)
        assert panel.calls == []
        [row] = await _rows(env)
        assert (row.status, row.attempts) == ("pending", 0)
        await _set_retry_at(env, datetime.now(UTC) - timedelta(seconds=1))
        await _wait_rows(env, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, env.server) == [_ms(target)]


async def test_unexpected_error_defers_record_by_same_backoff(env, monkeypatch):
    await _pay_during_outage(env)
    original = pending_updates._apply_to_server
    failures: list[int] = []

    async def poisoned(session, client, server, expiry, updater):
        if not failures:
            failures.append(client.id)
            raise RuntimeError("unexpected")
        return await original(session, client, server, expiry, updater)

    monkeypatch.setattr(pending_updates, "_apply_to_server", poisoned)
    report = await _run_once(env, MockPanelUpdater())
    assert report.updates_failed == 1
    [row] = await _rows(env)
    assert (row.status, row.attempts, row.last_error) == ("pending", 1, "RuntimeError: unexpected")
    remaining = row.next_retry_at - datetime.now(UTC)
    assert timedelta(seconds=55) < remaining <= timedelta(seconds=60)
    assert await _advisory(env) == (0, 0)  # исключение не оставило блокировку
    assert await _idle_in_transaction(env) == 0
    await _set_retry_at(env, None)
    assert (await _run_once(env, MockPanelUpdater())).updates_applied == 1


# --- Отключённый сервер ------------------------------------------------------------------------


async def _set_enabled(env: Env, enabled: bool) -> None:
    async with env.maker() as session:
        (await session.get(Server, env.server)).enabled = enabled
        await session.commit()


async def test_disabled_server_waits_and_applies_after_enable(env, wire, cycles):
    _, target = await _pay_during_outage(env)
    await _set_enabled(env, False)
    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_cycles(cycles, 5)
        assert panel.calls == []
        [row] = await _rows(env)
        assert (row.status, row.attempts, row.next_retry_at) == ("pending", 0, None)
        await _set_enabled(env, True)
        await _wait_rows(env, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, env.server) == [_ms(target)]


async def test_server_disabled_while_handler_waits_for_lock(env):
    """Сервер отключён, пока обработчик ждал блокировку: попытка не тратится."""
    _, target = await _pay_during_outage(env)
    async with env.engine.connect() as holder:
        await holder.execute(text("SELECT pg_advisory_lock(:c, :o)"),
                             {"c": LOCK_CLASS, "o": env.user})
        panel = MockPanelUpdater()
        waiting = asyncio.create_task(_run_once(env, panel))
        await _wait_lock_waiters(env)
        await _set_enabled(env, False)
        await holder.execute(text("SELECT pg_advisory_unlock(:c, :o)"),
                             {"c": LOCK_CLASS, "o": env.user})
        report = await waiting
    assert panel.calls == [] and report.updates_applied == 0
    [row] = await _rows(env)
    assert (row.status, row.attempts, row.next_retry_at) == ("pending", 0, None)
    await _set_enabled(env, True)
    assert (await _run_once(env, panel)).updates_applied == 1
    assert _expiry_calls(panel, env.server) == [_ms(target)]


# --- Фиксация результата до освобождения блокировки ----------------------------------------------


@pytest.mark.parametrize("kind", ["pending", "confirmed"])
async def test_result_committed_before_lock_release(env, monkeypatch, kind):
    if kind == "pending":
        await _pay_during_outage(env)
    else:
        payment_id, _ = await _crash_during_confirmation(env)
    original = operation_lock.user_operation
    snapshots: list[dict] = []

    @asynccontextmanager
    async def observed(session, user_id):
        async with original(session, user_id):
            yield
            # Тело операции завершено, advisory lock ещё удерживается.
            async with env.engine.connect() as conn:
                pending = (await conn.scalars(
                    text("SELECT status FROM pending_server_updates ORDER BY id")
                )).all()
                payments = (await conn.scalars(
                    text("SELECT status FROM payment_requests ORDER BY id")
                )).all()
            snapshots.append({
                "locks": await _advisory(env),
                "writers": await _uncommitted_writers(env),
                "pending": list(pending),
                "payments": list(payments),
            })

    monkeypatch.setattr(operation_lock, "user_operation", observed)
    report = await _run_once(env, MockPanelUpdater())

    assert report.changed
    assert snapshots, "операция не проходила через блокировку пользователя"
    for snapshot in snapshots:
        assert snapshot["locks"] == (1, 0)
        assert snapshot["writers"] == 0  # всё записанное уже зафиксировано
    if kind == "pending":
        assert snapshots[-1]["pending"] == ["applied"]
    else:
        assert (await _payment(env, payment_id)).status == PaymentStatus.APPLIED
        assert snapshots[0]["payments"] == [PaymentStatus.APPLIED.name]
    assert await _advisory(env) == (0, 0)


# --- Отмена worker'а и перезапуск --------------------------------------------------------------


async def test_cancel_worker_during_panel_call_and_restart(env, wire):
    _, target = await _pay_during_outage(env)
    hanging = _HangingPanel()
    wire(hanging)
    tasks = app_main.start_background_tasks(object(), _settings())
    await asyncio.wait_for(hanging.entered.wait(), 5)
    assert await _advisory(env) == (1, 0)  # worker держит блокировку у панели
    await asyncio.wait_for(app_main.stop_background_tasks(tasks), 5)
    assert hanging.cancelled.is_set() and all(task.done() for task in tasks)

    assert await _advisory(env) == (0, 0)
    assert await _idle_in_transaction(env) == 0
    [row] = await _rows(env)
    assert (row.status, row.attempts) == ("pending", 0)

    panel = MockPanelUpdater()
    wire(panel)
    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_rows(env, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, env.server) == [_ms(target)]
    assert await _audit(env, "pending_server_update.applied") == 1


async def test_cancel_worker_waiting_for_lock_and_restart(env, wire):
    """Блокировку держит другой процесс; отменённый worker не оставляет ожидание."""
    _, target = await _pay_during_outage(env)
    panel = MockPanelUpdater()
    wire(panel)
    async with env.engine.connect() as holder:
        await holder.execute(text("SELECT pg_advisory_lock(:c, :o)"),
                             {"c": LOCK_CLASS, "o": env.user})
        tasks = app_main.start_background_tasks(object(), _settings())
        await _wait_lock_waiters(env)
        await asyncio.wait_for(app_main.stop_background_tasks(tasks), 5)
        assert all(task.done() for task in tasks)
        async with asyncio.timeout(5):
            while await _advisory(env) != (1, 0):  # ожидание снято, держит только holder
                await asyncio.sleep(0.01)
        await holder.execute(text("SELECT pg_advisory_unlock(:c, :o)"),
                             {"c": LOCK_CLASS, "o": env.user})
    assert await _advisory(env) == (0, 0)
    assert panel.calls == []
    [row] = await _rows(env)
    assert (row.status, row.attempts) == ("pending", 0)

    tasks = app_main.start_background_tasks(object(), _settings())
    try:
        await _wait_rows(env, "applied")
    finally:
        await app_main.stop_background_tasks(tasks)
    assert _expiry_calls(panel, env.server) == [_ms(target)]
