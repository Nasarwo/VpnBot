"""Смена эпохи счётчика whitelist-панели при неприменённых событиях учёта.

Внешний ``resetTraffic`` или пересоздание клиента, пока расход ждёт решения
администратора (``uncertain``), не должны увеличивать доступный объём: проверяется
реальная квота панели и доступный на ней трафик, а не только запись о конфликте.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import texts
from app.db.enums import PaymentStatus, Protocol
from app.db.models import PaymentRequest, Server, ServerInbound
from app.services import whitelist
from app.services.panel_updater import MockPanelUpdater, QuotaClientState
from tests.test_whitelist import (  # noqa: F401
    EMAIL,
    _account,
    _ago,
    _baseline,
    _buy,
    _ledger_count,
    _pay,
    _wl_state,
    panel,
    service_on,
    wl_server,
)

GIB = whitelist.GIB


def _available(mock, server) -> int:
    """Трафик, который панель ещё пропустит: 0 у выключенного клиента."""
    state = _wl_state(mock, server)
    if not state.enable:
        return 0
    return max(0, state.total_bytes - (state.used_bytes or 0))


async def _uncertain_renewal(session, user, mock, server, used_gb: int) -> None:
    """Подтверждено 2 + 15 ГиБ на счётчике used_gb; продление при недоступной
    статистике, после него 5 ГиБ расхода — событие неопределённо.

    Нижняя граница остатка — 20 ГиБ: вариант «после» (5 + 15) меньше варианта
    «до» (10 + 12).
    """
    await _baseline(session, user, mock, server, 2, 15, used_gb=used_gb)
    mock.read_fail_server_ids.add(server.id)
    await _pay(session, user, mock, now=_ago(30))
    mock.consume(server.id, EMAIL, 5 * GIB, at=_ago(20))
    mock.read_fail_server_ids.clear()
    overview = await whitelist.user_overview(session, user.id, mock)
    assert overview.uncertain
    await whitelist.process_due(session, mock)
    state = _wl_state(mock, server)
    assert (state.total_bytes, state.used_bytes) == ((used_gb + 25) * GIB, (used_gb + 5) * GIB)
    assert _available(mock, server) == 20 * GIB


async def test_reset_with_uncertain_event_does_not_grow_available_volume(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    """Подтверждённый сценарий ревью: 100 ГиБ, 2 + 15, продление, 5 ГиБ, resetTraffic."""
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=100)
    regular_calls = list(panel.calls)

    panel.reset_traffic(wl_server.id, EMAIL)
    await whitelist.sync_user(session, user.id, panel)

    # Прежняя база (100 ГиБ) не стала трафиком, неразделённые 5 ГиБ по-прежнему
    # вычтены: квота новой эпохи — гарантированный минимум, как до сброса.
    state = _wl_state(panel, wl_server)
    assert (state.total_bytes, state.used_bytes, state.enable) == (20 * GIB, 0, True)
    assert _available(panel, wl_server) == 20 * GIB
    account = await _account(session, user)
    assert account.conflict and "сброшен" in account.conflict
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    assert await _ledger_count(session, user.id, "usage_rebase") == 1
    assert await _ledger_count(session, user.id, "free_grant") == 2  # обе оплаты в журнале
    events = await whitelist.list_open_events(session, user.id)
    assert [e.status for e in events] == ["uncertain"]
    # Варианты решения те же: период прежней эпохи прочитан до сброса.
    assert whitelist.uncertain_outcomes(account, events) == (
        (10 * GIB, 12 * GIB), (5 * GIB, 15 * GIB)
    )
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.uncertain and overview.status == "active"
    account = await _account(session, user)
    card = texts.admin_whitelist_user(
        user, account, overview, events, whitelist.uncertain_outcomes(account, events)
    )
    assert "Период прочитан до сброса счётчика" in card
    assert f"расход прежней эпохи 5 ГБ ({5 * GIB} байт)" in card

    # Повторы синхронизации, сверки и очереди не меняют состояние и журнал.
    for _ in range(2):
        await whitelist.sync_user(session, user.id, panel)
        await whitelist.reconcile_usage(session, panel)
        await whitelist.process_due(session, panel)
    assert await _ledger_count(session, user.id, "usage_rebase") == 1
    assert _wl_state(panel, wl_server).total_bytes == 20 * GIB

    # Граница действительно ограничивает доступ: панель выключает клиента.
    panel.consume(wl_server.id, EMAIL, 25 * GIB)
    await whitelist.reconcile_usage(session, panel)
    await whitelist.process_due(session, panel)
    assert _available(panel, wl_server) == 0
    assert _wl_state(panel, wl_server).total_bytes == 20 * GIB
    # Обычные конфиги не получают квоту и не трогаются.
    assert {server_id for server_id, *_ in panel.quota_applied} == {wl_server.id}
    assert panel.calls == regular_calls


@pytest.mark.parametrize(
    ("choice", "expected"),
    # Конец прочитанного периода: «до» — 10 + 12, «после» — 5 + 15; затем 8 ГиБ
    # расхода новой эпохи списываются с выбранного варианта.
    [("before", (2 * GIB, 12 * GIB)), ("after", (0, 12 * GIB))],
)
async def test_admin_resolution_after_reset_charges_new_epoch_usage(
    session, user, vpn_client, service_on, panel, wl_server, choice, expected  # noqa: F811
):
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=0)
    panel.reset_traffic(wl_server.id, EMAIL)
    await whitelist.sync_user(session, user.id, panel)
    assert _available(panel, wl_server) == 20 * GIB
    # Счётчик новой эпохи перерос верхнюю границу периода прежней (5 ГиБ).
    panel.consume(wl_server.id, EMAIL, 8 * GIB)

    await whitelist.resolve_uncertain(
        session, user.id, choice=choice, actor_user_id=None, reason="сброс", updater=panel
    )
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == expected
    # Точка — счётчик новой эпохи, а не граница периода прежней (5 ГиБ).
    assert account.usage_checkpoint_bytes == 8 * GIB
    assert await whitelist.list_open_events(session, user.id) == []
    state = _wl_state(panel, wl_server)
    assert state.total_bytes == 8 * GIB + sum(expected)
    assert _available(panel, wl_server) == sum(expected)
    with pytest.raises(whitelist.WhitelistError):
        await whitelist.resolve_uncertain(
            session, user.id, choice=choice, actor_user_id=None, reason="x", updater=panel
        )


async def test_admin_adjust_after_reset_sets_balances_on_new_counter(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=100)
    panel.reset_traffic(wl_server.id, EMAIL)
    await whitelist.sync_user(session, user.id, panel)
    panel.consume(wl_server.id, EMAIL, 3 * GIB)

    await whitelist.adjust_balance(
        session, user.id, free_bytes=4 * GIB, paid_bytes=12 * GIB, actor_user_id=None,
        reason="разбор сброса", updater=panel,
    )
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (4 * GIB, 12 * GIB)
    assert account.usage_checkpoint_bytes == 3 * GIB
    assert account.conflict is None
    assert await whitelist.list_open_events(session, user.id) == []
    assert _wl_state(panel, wl_server).total_bytes == 3 * GIB + 16 * GIB
    assert _available(panel, wl_server) == 16 * GIB


async def test_recreated_client_without_counter_decrease_is_new_epoch(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    """Пересоздание клиента: значение не уменьшилось, сменилась строка статистики."""
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=1)
    old_row = _wl_state(panel, wl_server).traffic_row_id
    panel.recreate(wl_server.id, EMAIL)
    panel.consume(wl_server.id, EMAIL, 7 * GIB)  # 7 ≥ последнего чтения (6)
    assert _wl_state(panel, wl_server).traffic_row_id != old_row

    await whitelist.sync_user(session, user.id, panel)

    # Минимум 20 ГиБ на конец прежней эпохи; 7 ГиБ новой эпохи уже израсходованы.
    state = _wl_state(panel, wl_server)
    assert (state.total_bytes, state.used_bytes) == (20 * GIB, 7 * GIB)
    assert _available(panel, wl_server) == 13 * GIB
    account = await _account(session, user)
    assert account.traffic_row_id == state.traffic_row_id
    assert account.conflict and f"строка {old_row}" in account.conflict
    assert await _ledger_count(session, user.id, "usage_rebase") == 1


async def test_reset_detected_against_last_reading_while_uncertain(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    """Сброс обнаруживается по последнему прочитанному значению, а не только по
    границе неопределённого периода, которая устаревает до решения администратора."""
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=10)
    panel.consume(wl_server.id, EMAIL, 10 * GIB)  # счётчик 25 после периода [10, 15]
    await whitelist.reconcile_usage(session, panel)
    assert _available(panel, wl_server) == 10 * GIB

    panel.reset_traffic(wl_server.id, EMAIL)
    panel.consume(wl_server.id, EMAIL, 20 * GIB)  # 20 ≥ 15, но < 25
    await whitelist.sync_user(session, user.id, panel)

    # До сброса оставалось 10 ГиБ; 20 ГиБ новой эпохи их исчерпали.
    state = _wl_state(panel, wl_server)
    assert state.total_bytes == 10 * GIB
    assert _available(panel, wl_server) == 0
    assert await _ledger_count(session, user.id, "usage_rebase") == 1


async def test_account_migrated_without_last_reading_detects_reset_by_event_bounds(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    """Строка до миграции f3a4b5c6d7e8: последнее чтение есть только в границах события."""
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=100)
    account = await _account(session, user)
    account.usage_observed_bytes = None
    account.usage_observed_at = None
    await session.commit()
    panel.reset_traffic(wl_server.id, EMAIL)
    panel.consume(wl_server.id, EMAIL, 101 * GIB)  # больше точки (100), меньше границы (105)

    await whitelist.sync_user(session, user.id, panel)

    state = _wl_state(panel, wl_server)
    assert state.total_bytes == 20 * GIB and _available(panel, wl_server) == 0
    assert await _ledger_count(session, user.id, "usage_rebase") == 1
    assert (await _account(session, user)).usage_observed_bytes == 101 * GIB


async def test_stale_batch_reading_while_uncertain_is_not_a_reset(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=100)
    stale = await panel.read_quota_client(wl_server, EMAIL)  # пакетное чтение: 105
    read_at = _ago(1)
    panel.consume(wl_server.id, EMAIL, 2 * GIB)
    await whitelist.user_overview(session, user.id, panel)  # другая операция: 107

    outcome = await whitelist._reconcile_one(session, user.id, stale, read_at)
    assert outcome is whitelist.ReconcileOutcome.BUSY
    assert await _ledger_count(session, user.id, "usage_rebase") == 0
    account = await _account(session, user)
    assert account.conflict is None and account.usage_checkpoint_bytes == 100 * GIB
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 125 * GIB


async def test_operation_started_before_batch_read_makes_it_stale(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    """Операция взяла время до пакетного чтения, а счётчик прочитала после него."""
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=100)
    started = datetime.now(UTC)
    stale = await panel.read_quota_client(wl_server, EMAIL)  # 105
    read_at = datetime.now(UTC)
    panel.consume(wl_server.id, EMAIL, 2 * GIB)
    await whitelist.sync_user(session, user.id, panel, now=started)  # прочитано 107

    outcome = await whitelist._reconcile_one(session, user.id, stale, read_at)
    assert outcome is whitelist.ReconcileOutcome.BUSY
    assert await _ledger_count(session, user.id, "usage_rebase") == 0
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 125 * GIB


@pytest.mark.parametrize(
    ("choice", "expected"),
    [("before", (7 * GIB, 57 * GIB)), ("after", (2 * GIB, 60 * GIB))],
)
async def test_several_open_events_purchase_after_conflict_and_restart(
    session, user, vpn_client, service_on, panel, wl_server, choice, expected  # noqa: F811
):
    await _baseline(session, user, panel, wl_server, 2, 15, used_gb=100)
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(40))
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(30))
    _, bought = await _buy(session, user, panel, 10, now=_ago(25))  # без чтения
    assert bought.applied
    panel.read_fail_server_ids.clear()
    await whitelist.user_overview(session, user.id, panel)
    panel.consume(wl_server.id, EMAIL, 2 * GIB, at=_ago(20))
    await _buy(session, user, panel, 25)  # точная привязка: 107
    events = await whitelist.list_open_events(session, user.id)
    assert [e.status for e in events] == ["uncertain", "pending", "pending"]
    await whitelist.process_due(session, panel)
    # 100 + (10 + 15 + 10 + 25); прочитано 107 → доступно 53.
    assert _wl_state(panel, wl_server).total_bytes == 160 * GIB
    assert _available(panel, wl_server) == 53 * GIB

    panel.reset_traffic(wl_server.id, EMAIL)
    panel.consume(wl_server.id, EMAIL, GIB)
    await whitelist.reconcile_usage(session, panel)  # сброс обнаружен и сохранён
    assert await _ledger_count(session, user.id, "usage_rebase") == 1
    # Рестарт до применения: новая сессия и новый процесс работы с панелью.
    restarted = MockPanelUpdater()
    restarted.quota_clients = panel.quota_clients
    maker = async_sessionmaker(bind=session.bind, expire_on_commit=False, class_=AsyncSession)
    async with maker() as fresh:
        assert await whitelist.process_due(fresh, restarted) == 1
        assert _wl_state(panel, wl_server).total_bytes == 53 * GIB
        assert _available(panel, wl_server) == 52 * GIB

        # Покупка после конфликта начисляется и сразу входит в квоту.
        payment, result = await _buy(fresh, user, restarted, 10)
        assert result.applied and result.whitelist_pending
        assert _wl_state(panel, wl_server).total_bytes == 63 * GIB
        assert _available(panel, wl_server) == 62 * GIB
        for _ in range(2):
            await whitelist.sync_user(fresh, user.id, restarted)
            await whitelist.reconcile_usage(fresh, restarted)
        assert await _ledger_count(fresh, user.id, "usage_rebase") == 1
        assert _available(panel, wl_server) == 62 * GIB

        await whitelist.resolve_uncertain(
            fresh, user.id, choice=choice, actor_user_id=None, reason="сброс",
            updater=restarted,
        )
        account = await _account(fresh, user)
        assert (account.free_bytes, account.paid_bytes) == expected
        assert account.usage_checkpoint_bytes == GIB
        assert await whitelist.list_open_events(fresh, user.id) == []
        assert _wl_state(panel, wl_server).total_bytes == GIB + sum(expected)
        assert await _ledger_count(fresh, user.id, "purchase") == 3
        assert await _ledger_count(fresh, user.id, "free_grant") == 2
        waiting = (
            await fresh.scalars(
                select(PaymentRequest).where(PaymentRequest.user_id == user.id)
            )
        ).all()
        assert all(p.status == PaymentStatus.APPLIED for p in waiting)
        assert all(p.apply_pending_version is None for p in waiting)


async def test_lifetime_config_stays_unlimited_after_reset(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    vpn_client.expires_at = None
    vpn_client.is_active = True
    await session.commit()
    await whitelist.run_rollout(session, panel, include_ambiguous=False, actor_user_id=None)
    panel.consume(wl_server.id, EMAIL, 50 * GIB)
    await whitelist.user_overview(session, user.id, panel)
    panel.reset_traffic(wl_server.id, EMAIL)
    await whitelist.sync_user(session, user.id, panel)
    state = _wl_state(panel, wl_server)
    assert (state.total_bytes, state.enable, state.expiry_ms) == (0, True, 0)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "lifetime"


async def test_uncertain_period_of_replaced_server_is_not_resolved_on_new_counter(
    session, user, vpn_client, service_on, panel, wl_server  # noqa: F811
):
    """Границы периода прежней панели несравнимы со счётчиком новой."""
    await _uncertain_renewal(session, user, panel, wl_server, used_gb=0)
    wl_server.enabled = False
    await session.commit()
    new = Server(name="WL-2", panel_url="https://wl2.example", username="a", password="b",
                 purpose="whitelist", enabled=True, inventory_status="ready")
    session.add(new)
    await session.flush()
    session.add(ServerInbound(server_id=new.id, inbound_id=3, protocol=Protocol.VLESS))
    await session.commit()
    panel.quota_clients[(new.id, EMAIL)] = QuotaClientState(
        EMAIL, True, GIB, 1, [3], used_bytes=0, traffic_row_id=500
    )
    await whitelist.user_overview(session, user.id, panel)
    account = await _account(session, user)
    events = await whitelist.list_open_events(session, user.id)
    assert [(e.status, e.anchor_max_bytes) for e in events] == [("uncertain", None)]
    assert whitelist.uncertain_outcomes(account, events) is None
    with pytest.raises(whitelist.WhitelistError, match="wladjust"):
        await whitelist.resolve_uncertain(
            session, user.id, choice="before", actor_user_id=None, reason="x", updater=panel
        )
