"""Бизнес-правила услуги «Обход белых списков» на модели панели (MockPanelUpdater)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.config import Settings
from app.db.enums import AttachmentType, PaymentStatus, Protocol, UserRole
from app.db.models import (
    PAYMENT_KIND_TRAFFIC,
    ClientServerMapping,
    PaymentRequest,
    Server,
    ServerInbound,
    TrafficPackage,
    User,
    VpnClient,
    WhitelistAccount,
    WhitelistLedger,
)
from app.db.repositories import ServerRepository
from app.services import billing, payments, provisioning, whitelist
from app.services.access import resolve_effective_role
from app.services.panel_updater import MockPanelUpdater, QuotaClientState
from tests.whitelist_inbounds import vless_reality

GIB = whitelist.GIB
EMAIL = "test@local"  # идентичность mapping'а из фикстуры vpn_client


@pytest_asyncio.fixture
async def wl_server(session) -> Server:
    srv = Server(
        name="Обход белых списков",
        panel_url="https://wl.example:2053",
        username="admin",
        password="secret",
        purpose="whitelist",
        enabled=True,
        inventory_status="ready",
    )
    session.add(srv)
    await session.flush()
    session.add(
        ServerInbound(
            server_id=srv.id, inbound_id=7, protocol=Protocol.VLESS, enabled=True,
            remark="Обход белых списков",
        )
    )
    await session.commit()
    return srv


@pytest_asyncio.fixture
async def service_on(session, wl_server):
    config = await whitelist.get_config(session)
    config.service_enabled = True
    await whitelist.ensure_defaults(session)
    return config


@pytest_asyncio.fixture
def panel() -> MockPanelUpdater:
    return MockPanelUpdater()


async def _pay(session, user, panel, days=30, amount=175, now=None):
    payment = await payments.create_request(session, user.id, amount, days)
    result = await billing.confirm_payment(session, payment.id, None, panel, now=now)
    assert result.applied
    return payment, result


async def _account(session, user) -> WhitelistAccount:
    account = await whitelist.get_account(session, user.id)
    assert account is not None
    return account


def _wl_state(panel, wl_server) -> QuotaClientState:
    return panel.quota_clients[(wl_server.id, EMAIL)]


async def _set_balance(session, user, panel, free_gb, paid_gb):
    account = await _account(session, user)
    account.free_bytes = int(free_gb * GIB)
    account.paid_bytes = int(paid_gb * GIB)
    whitelist.mark_dirty(account)
    await session.commit()
    await whitelist.sync_user(session, user.id, panel)


async def _package(session, size_gb) -> TrafficPackage:
    return await session.scalar(
        select(TrafficPackage).where(TrafficPackage.traffic_bytes == size_gb * GIB)
    )


async def _buy(session, user, panel, size_gb=25, now=None):
    package = await _package(session, size_gb)
    payment = await payments.create_traffic_request(session, user.id, package.id)
    result = await billing.confirm_payment(session, payment.id, None, panel, now=now)
    return payment, result


async def _ledger_count(session, user_id, kind=None) -> int:
    query = select(func.count(WhitelistLedger.id)).where(WhitelistLedger.user_id == user_id)
    if kind:
        query = query.where(WhitelistLedger.kind == kind)
    return await session.scalar(query)


# --- 1–6: бесплатный пакет ------------------------------------------------------


@pytest_asyncio.fixture
async def std_target(session, server) -> Server:
    session.add(ServerInbound(server_id=server.id, inbound_id=1, protocol=Protocol.VLESS))
    await session.commit()
    return server


async def test_trial_grants_three_gb_exactly_once(session, user, std_target, service_on, panel):
    result = await billing.grant_trial(session, user.id, panel, period_days=3)
    assert result.applied
    account = await _account(session, user)
    assert account.free_bytes == 3 * GIB
    assert account.paid_bytes == 0
    assert (await billing.grant_trial(session, user.id, panel, period_days=3)).already_used
    assert not await whitelist.grant_for_trial(session, user.id, panel)
    assert await _ledger_count(session, user.id, "free_grant") == 1
    # Конфиг создан на whitelist-панели с квотой 3 ГБ, обычный сервер — безлимит.
    wl = await whitelist.get_active_server(session)
    state = panel.quota_clients[(wl.id, account.panel_email)]
    assert state.total_bytes == 3 * GIB and state.enable
    assert std_target.id not in {sid for sid, *_ in panel.quota_applied}


async def test_rollout_gives_paid_ten_gb_once_and_keeps_purchased(
    session, user, vpn_client, service_on, panel
):
    config = await whitelist.get_config(session)
    config.service_enabled = False
    vpn_client.expires_at = datetime.now(UTC) + timedelta(days=20)
    vpn_client.is_active = True
    session.add(PaymentRequest(
        user_id=user.id, amount=175, period_days=30, payment_code="PAY-OLD",
        status=PaymentStatus.APPLIED, target_expires_at=vpn_client.expires_at,
    ))
    await session.commit()

    plan = await whitelist.rollout_plan(session)
    assert plan.counts == {"paid": 1}
    report = await whitelist.run_rollout(
        session, panel, include_ambiguous=False, actor_user_id=None
    )
    assert report.granted == {"paid": 1}
    account = await _account(session, user)
    assert account.free_bytes == 10 * GIB

    account.paid_bytes = 7 * GIB
    whitelist.mark_dirty(account)
    await session.commit()
    panel.consume(wl_id := (await whitelist.get_active_server(session)).id, EMAIL, GIB)
    await whitelist.user_overview(session, user.id, panel)
    report = await whitelist.run_rollout(
        session, panel, include_ambiguous=True, actor_user_id=None
    )
    assert report.granted == {} and report.skipped_existing == 1
    account = await _account(session, user)
    assert account.free_bytes == 9 * GIB
    assert account.paid_bytes == 7 * GIB
    assert await _ledger_count(session, user.id, "rollout") == 1
    assert panel.quota_clients[(wl_id, EMAIL)].total_bytes == GIB + 16 * GIB


async def test_usage_spends_free_first_then_purchased(session, user, vpn_client, service_on,
                                                      panel, wl_server):
    await _pay(session, user, panel)
    await _set_balance(session, user, panel, 3, 20)
    assert _wl_state(panel, wl_server).total_bytes == 23 * GIB
    panel.consume(wl_server.id, EMAIL, 5 * GIB)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert (overview.free_bytes, overview.paid_bytes) == (0, 18 * GIB)
    # Уже учтённый расход повторно не списывается.
    overview = await whitelist.user_overview(session, user.id, panel)
    assert (overview.free_bytes, overview.paid_bytes) == (0, 18 * GIB)
    assert whitelist.apply_usage(3 * GIB, 20 * GIB, 5 * GIB) == (0, 18 * GIB)
    assert whitelist.apply_usage(3, 20, 2) == (1, 20)
    assert whitelist.apply_usage(3, 2, 10) == (0, 0)


async def test_subscription_payment_replaces_free_and_keeps_purchased(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    await _set_balance(session, user, panel, 2, 15)
    await _pay(session, user, panel)
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 15 * GIB)
    assert _wl_state(panel, wl_server).total_bytes == 25 * GIB


async def test_payment_settles_usage_before_replacing_free(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    await _set_balance(session, user, panel, 2, 15)
    panel.consume(wl_server.id, EMAIL, 5 * GIB)  # 2 бесплатных + 3 купленных
    await _pay(session, user, panel)
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 12 * GIB)
    assert _wl_state(panel, wl_server).total_bytes == 5 * GIB + 22 * GIB


async def test_trial_to_paid_resets_free_to_paid_package_without_adding(
    session, user, std_target, service_on, panel
):
    await billing.grant_trial(session, user.id, panel, period_days=3)
    await _pay(session, user, panel)
    account = await _account(session, user)
    assert account.free_bytes == 10 * GIB


async def test_multi_month_payment_grants_one_package_and_no_monthly_reset(
    session, user, vpn_client, service_on, panel, wl_server
):
    payment, _ = await _pay(session, user, panel, days=180, amount=850)
    assert await _ledger_count(session, user.id, "free_grant") == 1
    panel.consume(wl_server.id, EMAIL, 4 * GIB)
    later = datetime.now(UTC) + timedelta(days=40)
    await whitelist.user_overview(session, user.id, panel, now=later)
    await whitelist.process_due(session, panel)
    await billing.sync_client(session, vpn_client.id, None, panel)
    account = await _account(session, user)
    assert account.free_bytes == 6 * GIB
    assert await _ledger_count(session, user.id, "free_grant") == 1


async def test_manual_extend_and_sync_do_not_grant_package(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, GIB)
    await billing.manual_extend(session, vpn_client.id, 30, None, panel)
    await billing.sync_client(session, vpn_client.id, None, panel)
    account = await _account(session, user)
    assert account.free_bytes == 9 * GIB
    assert await _ledger_count(session, user.id, "free_grant") == 1
    # Новый срок перенесён на конфиг.
    expiry = vpn_client.expires_at.replace(tzinfo=UTC)
    assert _wl_state(panel, wl_server).expiry_ms == int(expiry.timestamp() * 1000)


# --- 7–12: покупка и ограничения ------------------------------------------------


async def test_purchase_adds_only_purchased_traffic(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    expires = vpn_client.expires_at
    payment, result = await _buy(session, user, panel, 25)
    assert result.applied and result.traffic_bytes == 25 * GIB
    assert payment.kind == PAYMENT_KIND_TRAFFIC and payment.period_days == 0
    assert payment.status == PaymentStatus.APPLIED
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 25 * GIB)
    assert vpn_client.expires_at == expires
    assert _wl_state(panel, wl_server).total_bytes == 35 * GIB


async def test_expired_subscription_stops_config_and_keeps_traffic(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    await _buy(session, user, panel, 10)
    vpn_client.expires_at = datetime.now(UTC) - timedelta(days=1)
    await session.commit()
    await whitelist.after_access_change(session, user.id, panel)
    state = _wl_state(panel, wl_server)
    assert not state.enable
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "expired" and overview.paid_bytes == 10 * GIB
    assert not overview.can_buy
    await _pay(session, user, panel)
    account = await _account(session, user)
    assert account.paid_bytes == 10 * GIB
    assert _wl_state(panel, wl_server).enable


async def test_expiry_between_request_and_confirmation_still_credits(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    package = await _package(session, 25)
    payment = await payments.create_traffic_request(session, user.id, package.id)
    vpn_client.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await session.commit()
    result = await billing.confirm_payment(session, payment.id, None, panel)
    assert result.applied
    account = await _account(session, user)
    assert account.paid_bytes == 25 * GIB
    assert not _wl_state(panel, wl_server).enable


async def test_exhaustion_disables_only_whitelist_config_and_purchase_resumes(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    regular_calls = list(panel.calls)
    panel.consume(wl_server.id, EMAIL, 11 * GIB)
    assert not _wl_state(panel, wl_server).enable  # панель отключила по квоте
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "exhausted"
    await whitelist.process_due(session, panel)
    state = _wl_state(panel, wl_server)
    assert not state.enable and state.total_bytes == 11 * GIB  # не 0 = безлимит
    assert panel.calls == regular_calls  # обычные серверы не трогались
    assert vpn_client.is_active
    await _buy(session, user, panel, 10)
    state = _wl_state(panel, wl_server)
    assert state.enable and state.total_bytes == 21 * GIB


async def test_lifetime_access_is_unlimited_without_admin_role(
    session, user, vpn_client, service_on, panel, wl_server
):
    vpn_client.expires_at = None
    vpn_client.is_active = True
    await session.commit()
    await whitelist.run_rollout(session, panel, include_ambiguous=False, actor_user_id=None)
    state = _wl_state(panel, wl_server)
    assert (state.total_bytes, state.enable, state.expiry_ms) == (0, True, 0)
    assert resolve_effective_role(Settings(admin_telegram_ids=[]), user.telegram_id,
                                  vpn_client) == UserRole.USER
    package = await _package(session, 10)
    with pytest.raises(payments.PaymentRequestError):
        await payments.create_traffic_request(session, user.id, package.id)
    panel.consume(wl_server.id, EMAIL, 50 * GIB)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "lifetime" and _wl_state(panel, wl_server).enable


async def test_package_change_does_not_alter_created_request(
    session, user, vpn_client, service_on, panel
):
    await _pay(session, user, panel)
    package = await _package(session, 25)
    payment = await payments.create_traffic_request(session, user.id, package.id)
    await whitelist.save_package(
        session, package_id=package.id, size_bytes=30 * GIB, price=Decimal("120"),
        actor_user_id=None,
    )
    await session.refresh(payment)
    assert payment.traffic_bytes == 25 * GIB and payment.amount == Decimal("99")
    await billing.confirm_payment(session, payment.id, None, panel)
    assert (await _account(session, user)).paid_bytes == 25 * GIB


# --- 13–15: повторы, сбои, счётчик ----------------------------------------------


async def test_repeated_confirmation_and_queue_do_not_duplicate_credit(
    session, user, vpn_client, service_on, wl_server
):
    working = MockPanelUpdater()
    await _pay(session, user, working)
    down = MockPanelUpdater(fail_server_ids={wl_server.id})
    down.quota_clients = working.quota_clients
    payment, result = await _buy(session, user, down, 25)
    assert result.applied and result.whitelist_pending
    await session.refresh(payment)
    assert payment.apply_pending_version is not None and payment.last_error is None
    again = await billing.confirm_payment(session, payment.id, None, down)
    assert again.already_applied
    again = await billing.retry_payment(session, payment.id, None, down)
    assert again.already_applied
    account = await _account(session, user)
    # Начисление сохранено один раз и ждёт сверки расхода; остаток не тронут.
    events = await whitelist.list_open_events(session, user.id)
    assert [e.paid_delta for e in events] == [25 * GIB]
    assert account.paid_bytes == 0 and account.desired_version > account.applied_version
    account.next_sync_at = None
    await session.commit()
    assert await whitelist.process_due(session, working) == 1
    assert await whitelist.process_due(session, working) == 0
    account = await _account(session, user)
    assert account.paid_bytes == 25 * GIB
    assert working.quota_clients[(wl_server.id, EMAIL)].total_bytes == 35 * GIB
    assert await _ledger_count(session, user.id, "purchase") == 1


async def test_restart_between_commit_and_panel_does_not_regrant(
    session, user, vpn_client, service_on, panel, wl_server
):
    wl_id = wl_server.id
    await _pay(session, user, panel)
    panel.consume(wl_id, EMAIL, 4 * GIB)
    payment = await payments.create_request(session, user.id, 175, 30)

    class Interrupted(MockPanelUpdater):
        async def update_expiry(self, *_args):
            raise RuntimeError("process interrupted after durable commit")

    interrupted = Interrupted()
    interrupted.quota_clients = panel.quota_clients
    with pytest.raises(RuntimeError):
        await billing.confirm_payment(session, payment.id, None, interrupted)
    await session.rollback()
    await session.refresh(payment)
    await session.refresh(user)
    assert payment.status == PaymentStatus.CONFIRMED
    account = await _account(session, user)
    assert account.free_bytes == 10 * GIB  # выдача сохранена вместе с target
    panel.consume(wl_id, EMAIL, GIB)
    result = await billing.retry_payment(session, payment.id, None, panel)
    assert result.applied
    account = await _account(session, user)
    assert account.free_bytes == 9 * GIB  # повтор не восстановил пакет
    assert await _ledger_count(session, user.id, "free_grant") == 2


async def test_stale_retry_cannot_roll_back_newer_state(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    down = MockPanelUpdater(fail_server_ids={wl_server.id})
    down.quota_clients = panel.quota_clients
    await _buy(session, user, down, 10)
    await _buy(session, user, panel, 25)  # более поздняя покупка применена
    account = await _account(session, user)
    account.next_sync_at = None
    await session.commit()
    await whitelist.process_due(session, panel)  # «старая» задача
    assert _wl_state(panel, wl_server).total_bytes == 45 * GIB
    assert (await _account(session, user)).paid_bytes == 35 * GIB


async def test_stats_failure_shows_stale_state_without_changes(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, 2 * GIB)
    panel.read_fail_server_ids.add(wl_server.id)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.stale and overview.free_bytes == 10 * GIB
    panel.read_fail_server_ids.clear()
    overview = await whitelist.user_overview(session, user.id, panel)
    assert not overview.stale and overview.free_bytes == 8 * GIB


@pytest.mark.parametrize("operation", ["reset_traffic", "recreate"])
async def test_counter_decrease_is_not_new_traffic(
    session, user, vpn_client, service_on, panel, wl_server, operation
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, 6 * GIB)
    await whitelist.user_overview(session, user.id, panel)
    assert (await _account(session, user)).free_bytes == 4 * GIB
    getattr(panel, operation)(wl_server.id, EMAIL)
    panel.consume(wl_server.id, EMAIL, GIB)
    await whitelist.user_overview(session, user.id, panel)
    account = await _account(session, user)
    assert account.free_bytes == 3 * GIB  # расход новой эпохи списан, база не вернулась
    assert account.conflict and "сброшен" in account.conflict
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == GIB + 3 * GIB
    assert await _ledger_count(session, user.id, "usage_rebase") == 1


async def test_background_reconcile_detects_reset_and_ignores_stale_reading(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, 6 * GIB)
    assert await whitelist.reconcile_usage(session, panel) == 0
    assert (await _account(session, user)).free_bytes == 4 * GIB
    panel.reset_traffic(wl_server.id, EMAIL)
    assert await whitelist.reconcile_usage(session, panel) == 1
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 4 * GIB
    # Чтение, сделанное до более новой сверки, не применяется.
    old = QuotaClientState(EMAIL, True, 1, 1, [7], used_bytes=0, traffic_row_id=1)
    assert await whitelist._reconcile_one(
        session, user.id, old, datetime.now(UTC) - timedelta(hours=1)
    ) is whitelist.ReconcileOutcome.BUSY


def test_exhausted_limit_never_becomes_unlimited():
    account = WhitelistAccount(user_id=1, free_bytes=0, paid_bytes=0,
                               usage_checkpoint_bytes=None, admin_blocked=False)
    now = datetime.now(UTC)
    access = whitelist.AccessState(lifetime=False, active=True, expires_at=now + timedelta(1))
    target = whitelist.compute_target(account, access, now)
    assert target.total_bytes == 1 and not target.enable
    account.usage_checkpoint_bytes = 5 * GIB
    assert whitelist.compute_target(account, access, now).total_bytes == 5 * GIB
    account.paid_bytes = 3 * GIB
    target = whitelist.compute_target(account, access, now)
    assert target.total_bytes == 8 * GIB and target.enable
    assert target.expiry_ms == int(access.expires_at.timestamp() * 1000)


# --- 17–18: сервер, импорт, ручные отключения ------------------------------------


class _Panel:
    def __init__(self, inbounds=None, error=None):
        self.inbounds = inbounds or []
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def list_inbounds(self):
        if self.error:
            raise self.error
        return self.inbounds


async def test_first_import_failure_then_retry_and_single_target(session, monkeypatch, panel):
    from app.services.xui_client import XuiError

    server = Server(name="WL", panel_url="https://cc.example", username="a", password="b",
                    purpose="whitelist", enabled=True)
    session.add(server)
    await session.commit()
    monkeypatch.setattr(provisioning, "XuiClient",
                        lambda **_: _Panel(error=XuiError("timeout")))
    result = await whitelist.sync_inventory(session, server)
    await session.commit()
    assert result.status == "error" and not whitelist.server_ready(server)
    assert await whitelist.process_due(session, panel) == 0

    two = [vless_reality(3, remark="A"), vless_reality(4, remark="B")]
    monkeypatch.setattr(provisioning, "XuiClient", lambda **_: _Panel(two))
    result = await whitelist.sync_inventory(session, server)
    await session.commit()
    server = await whitelist.get_active_server(session)
    assert result.status == "needs_choice" and not whitelist.server_ready(server)
    await whitelist.choose_inbound(session, server, 4, None)
    server = await whitelist.get_active_server(session)
    assert whitelist.server_ready(server) and whitelist.target_inbound(server).inbound_id == 4

    three = [*two, vless_reality(5)]
    monkeypatch.setattr(provisioning, "XuiClient", lambda **_: _Panel(three))
    for _ in range(2):  # повтор идемпотентен
        result = await whitelist.sync_inventory(session, server)
        await session.commit()
        server = await whitelist.get_active_server(session)
        assert result.status == "ready"
        assert whitelist.target_inbound(server).inbound_id == 4
    assert await session.scalar(select(func.count(WhitelistLedger.id))) == 0


async def test_whitelist_server_excluded_from_regular_provisioning(
    session, user, std_target, wl_server, service_on, panel
):
    servers = await ServerRepository(session).list_enabled_with_inbounds()
    assert [s.id for s in servers] == [std_target.id]
    assert [s.id for s in await ServerRepository(session).list_enabled()] == [std_target.id]
    await billing.grant_trial(session, user.id, panel, period_days=3)
    assert {sid for sid, *_ in panel.provisioned} == {std_target.id}
    session.add(ClientServerMapping(
        vpn_client_id=(await session.scalar(select(VpnClient.id))), server_id=wl_server.id,
        inbound_id=7, protocol=Protocol.VLESS, client_uuid="x", email="x",
    ))
    await session.commit()
    await billing.sync_client(session, await session.scalar(select(VpnClient.id)), None, panel)
    assert all(sid != wl_server.id for sid, _ in panel.calls)


async def test_manual_panel_disable_is_not_reenabled_by_reads_or_retries(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    _wl_state(panel, wl_server).enable = False  # администратор выключил на панели
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "blocked"
    await whitelist.process_due(session, panel)
    await whitelist.sync_user(session, user.id, panel)
    await _buy(session, user, panel, 10)
    assert not _wl_state(panel, wl_server).enable
    await whitelist.set_admin_block(session, user.id, False, None, panel)
    assert _wl_state(panel, wl_server).enable


async def _manual_disable(session, user, panel, wl_server) -> None:
    """Администратор выключил клиента на панели; бот это обнаружил."""
    _wl_state(panel, wl_server).enable = False
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "blocked"
    assert (await _account(session, user)).admin_blocked


async def test_explicit_unblock_applies_before_queue_runs(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    await _manual_disable(session, user, panel, wl_server)
    # Без промежуточного process_due/sync: панель ещё выключена вручную.
    outcome = await whitelist.set_admin_block(session, user.id, False, None, panel)
    assert outcome.applied
    account = await _account(session, user)
    assert not account.admin_blocked and account.conflict is None
    assert _wl_state(panel, wl_server).enable
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "active"
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).enable
    assert not (await _account(session, user)).admin_blocked


@pytest.mark.parametrize("failure", ["panel_down", "apply_fails_once"])
async def test_unblock_survives_unavailable_panel_and_queue_restores(
    session, user, vpn_client, service_on, panel, wl_server, monkeypatch, failure
):
    await _pay(session, user, panel)
    await _manual_disable(session, user, panel, wl_server)
    if failure == "panel_down":
        panel.fail_server_ids.add(wl_server.id)
    else:
        real_apply = panel.apply_quota_client
        calls = {"n": 0}

        async def flaky(server, spec, target):
            calls["n"] += 1
            if calls["n"] == 1:
                raise whitelist.PanelUpdateError("временный сбой")
            return await real_apply(server, spec, target)

        monkeypatch.setattr(panel, "apply_quota_client", flaky)
    outcome = await whitelist.set_admin_block(session, user.id, False, None, panel)
    assert not outcome.applied and outcome.pending
    account = await _account(session, user)
    assert not account.admin_blocked and account.desired_version > account.applied_version
    assert not _wl_state(panel, wl_server).enable
    # Чтение баланса и фоновый повтор при ещё выключенном клиенте не блокируют заново.
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status != "blocked" and not account.admin_blocked
    account.next_sync_at = datetime.now(UTC) - timedelta(seconds=1)
    await session.commit()
    if failure == "panel_down":
        assert await whitelist.process_due(session, panel) == 0
        assert not (await _account(session, user)).admin_blocked
        panel.fail_server_ids.clear()
        account = await _account(session, user)
        account.next_sync_at = None
        await session.commit()
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).enable
    assert not (await _account(session, user)).admin_blocked


async def test_unblock_does_not_bypass_expired_subscription(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    await _manual_disable(session, user, panel, wl_server)
    vpn_client.expires_at = datetime.now(UTC) - timedelta(days=1)
    await session.commit()
    await whitelist.set_admin_block(session, user.id, False, None, panel)
    assert not _wl_state(panel, wl_server).enable
    account = await _account(session, user)
    assert not account.admin_blocked
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "expired" and not account.admin_blocked
    await _pay(session, user, panel)
    assert _wl_state(panel, wl_server).enable


async def test_unblock_does_not_bypass_exhausted_quota(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    await _manual_disable(session, user, panel, wl_server)
    _wl_state(panel, wl_server).used_bytes = 11 * GIB  # квота исчерпана
    await whitelist.set_admin_block(session, user.id, False, None, panel)
    state = _wl_state(panel, wl_server)
    assert not state.enable and state.total_bytes == 11 * GIB
    account = await _account(session, user)
    assert not account.admin_blocked
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "exhausted" and not account.admin_blocked
    await _buy(session, user, panel, 10)
    assert _wl_state(panel, wl_server).enable


async def test_unblock_restores_lifetime_access(
    session, user, vpn_client, service_on, panel, wl_server
):
    vpn_client.expires_at = None
    vpn_client.is_active = True
    await session.commit()
    await whitelist.run_rollout(session, panel, include_ambiguous=False, actor_user_id=None)
    _wl_state(panel, wl_server).enable = False
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "blocked"
    await whitelist.set_admin_block(session, user.id, False, None, panel)
    state = _wl_state(panel, wl_server)
    assert (state.total_bytes, state.enable, state.expiry_ms) == (0, True, 0)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "lifetime"


async def test_disabled_server_is_not_touched(session, user, vpn_client, service_on, panel,
                                              wl_server):
    await _pay(session, user, panel)
    wl_server.enabled = False
    await session.commit()
    applied = len(panel.quota_applied)
    await _buy(session, user, panel, 10)
    await whitelist.process_due(session, panel)
    overview = await whitelist.user_overview(session, user.id, panel)
    assert len(panel.quota_applied) == applied
    # Расход клиента выключенного сервера не прочитать: покупка ждёт сверки.
    assert overview.paid_bytes == 0 and overview.pending
    assert overview.awaiting == [whitelist.AwaitingCredit(free_set=None, paid_delta=10 * GIB)]


async def test_second_enabled_whitelist_server_is_rejected(session, wl_server):
    from sqlalchemy.exc import IntegrityError

    assert await whitelist.has_other_enabled_whitelist(session)
    session.add(Server(name="WL2", panel_url="https://x", username="a", password="b",
                       purpose="whitelist", enabled=True))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
    session.add(Server(name="WL-old", panel_url="https://y", username="a", password="b",
                       purpose="whitelist", enabled=False))
    await session.commit()


# --- 19: идентичность подписки ----------------------------------------------------


async def test_whitelist_client_uses_subscription_identity(
    session, user, vpn_client, service_on, panel, wl_server
):
    user.telegram_id = 555
    await session.commit()
    await _pay(session, user, panel)
    state = _wl_state(panel, wl_server)
    assert state.email == EMAIL and state.inbound_ids == [7]
    account = await _account(session, user)
    assert account.panel_email == EMAIL
    # Mapping на whitelist-сервер не создаётся: обычные пути его не видят.
    mappings = (await session.scalars(select(ClientServerMapping))).all()
    assert all(m.server_id != wl_server.id for m in mappings)


# --- заявки, отмена, удаление -------------------------------------------------------


async def test_traffic_request_rules(session, user, vpn_client, service_on, panel):
    package = await _package(session, 10)
    with pytest.raises(payments.PaymentRequestError):
        await payments.create_traffic_request(session, user.id, package.id)  # нет подписки
    await _pay(session, user, panel)
    payment = await payments.create_traffic_request(session, user.id, package.id)
    await payments.attach_proof(
        session, payment.id, file_type=AttachmentType.TEXT, caption="ok"
    )
    with pytest.raises(payments.PendingRequestExists):
        await payments.create_traffic_request(session, user.id, package.id)
    assert await payments.cancel_open_request(session, user.id) is None
    rejected = await billing.reject_payment(session, payment.id, None)
    assert rejected.status == PaymentStatus.REJECTED


async def test_reject_after_credit_does_not_revert(session, user, vpn_client, service_on, panel):
    await _pay(session, user, panel)
    payment, _ = await _buy(session, user, panel, 10)
    await billing.reject_payment(session, payment.id, None)
    assert payment.status == PaymentStatus.APPLIED


async def test_subscription_delete_removes_panel_client_and_keeps_balance(
    session, user, vpn_client, service_on, panel, wl_server
):
    from app.services import subscription_delete

    await _pay(session, user, panel)
    await _buy(session, user, panel, 25)
    result = await subscription_delete.delete_user_subscription(session, user, panel)
    assert result.deleted
    assert (wl_server.id, EMAIL) not in panel.quota_clients
    account = await _account(session, user)
    assert account.paid_bytes == 25 * GIB and account.panel_email is None


async def test_user_deletion_cascades_accounts(session, user, vpn_client, service_on, panel):
    await _pay(session, user, panel)
    await session.delete(await session.get(User, user.id))
    await session.commit()
    assert await session.scalar(select(func.count(WhitelistAccount.id))) == 0


async def test_service_not_launched_grants_nothing(session, user, vpn_client, wl_server, panel):
    await _pay(session, user, panel)
    assert await whitelist.get_account(session, user.id) is None
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.status == "not_launched"


async def test_new_whitelist_server_starts_from_fresh_baseline(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, 6 * GIB)
    await whitelist.user_overview(session, user.id, panel)
    wl_server.enabled = False
    await session.commit()
    new = Server(name="WL-2", panel_url="https://wl2.example", username="a", password="b",
                 purpose="whitelist", enabled=True, inventory_status="ready")
    session.add(new)
    await session.flush()
    session.add(ServerInbound(server_id=new.id, inbound_id=3, protocol=Protocol.VLESS))
    await session.commit()
    await whitelist.sync_user(session, user.id, panel)
    targets = [t for sid, _, t in panel.quota_applied if sid == new.id]
    # Ни одна запись на новой панели не опиралась на счётчик старой (6 ГБ).
    assert targets and all(t.total_bytes == 4 * GIB for t in targets)
    account = await _account(session, user)
    assert account.server_id == new.id and account.free_bytes == 4 * GIB


async def test_unexpected_panel_error_after_commit_keeps_payment_and_queues(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _pay(session, user, panel)

    class Broken(MockPanelUpdater):
        async def apply_quota_client(self, *_args):
            raise RuntimeError("unexpected")

    broken = Broken()
    broken.quota_clients = panel.quota_clients
    payment, result = await _buy(session, user, broken, 10)
    assert result.applied and result.whitelist_pending
    await session.refresh(payment)
    assert payment.status == PaymentStatus.APPLIED
    account = await _account(session, user)
    assert account.paid_bytes == 10 * GIB
    assert account.desired_version > account.applied_version
    assert await whitelist.process_due(session, panel) == 1
    assert _wl_state(panel, wl_server).total_bytes == 20 * GIB


# --- Порядок событий при недоступной статистике -------------------------------


def _ago(minutes: int) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=minutes)


async def _baseline(session, user, panel, wl_server, free_gb, paid_gb, used_gb=0):
    """Подтверждённый учёт на T−60 мин: остатки сверены со счётчиком used_gb."""
    await _pay(session, user, panel)
    if used_gb:
        panel.consume(wl_server.id, EMAIL, used_gb * GIB, at=_ago(70))
        await whitelist.user_overview(session, user.id, panel)  # расход сверен
    await _set_balance(session, user, panel, free_gb, paid_gb)
    account = await _account(session, user)
    assert account.usage_checkpoint_bytes == used_gb * GIB
    account.last_synced_at = _ago(60)
    await session.commit()


async def _events(session, user):
    return (
        await session.scalars(
            select(WhitelistLedger)
            .where(WhitelistLedger.user_id == user.id)
            .where(WhitelistLedger.free_set.is_not(None) | WhitelistLedger.paid_delta.is_not(None))
            .order_by(WhitelistLedger.id)
            .execution_options(populate_existing=True)
        )
    ).all()


async def test_payment_during_stats_outage_settles_old_usage_before_new_package(
    session, user, vpn_client, service_on, panel, wl_server
):
    """Контрольный пример: 2 + 15, расход 5 до продления, статистика недоступна."""
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(40))  # до продления
    panel.read_fail_server_ids.add(wl_server.id)
    payment, result = await _pay(session, user, panel, now=_ago(30))

    # Оплата сохранена, но прежние остатки не заменены до сверки расхода.
    assert result.whitelist_pending
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    pending = await whitelist.list_open_events(session, user.id)
    assert [(e.status, e.free_set, e.anchor_bytes) for e in pending] == [
        ("pending", 10 * GIB, None)
    ]
    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.stale and (overview.free_bytes, overview.paid_bytes) == (2 * GIB, 15 * GIB)
    assert overview.awaiting == [whitelist.AwaitingCredit(free_set=10 * GIB, paid_delta=None)]
    # Квота на время ожидания — нижняя граница: точка 0 + 10 + 15.
    access = whitelist.access_state(vpn_client, datetime.now(UTC))
    target = whitelist.compute_target(account, access, datetime.now(UTC), pending)
    assert target.total_bytes == 25 * GIB and target.enable
    # Повтор подтверждения и фоновая очередь во время сбоя ничего не меняют.
    assert (await billing.confirm_payment(session, payment.id, None, panel)).already_applied
    await whitelist.process_due(session, panel)
    assert (await _account(session, user)).free_bytes == 2 * GIB

    panel.read_fail_server_ids.clear()
    overview = await whitelist.user_overview(session, user.id, panel)
    assert not overview.stale and overview.awaiting == []
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 12 * GIB)
    grant = (await _events(session, user))[-1]
    assert (grant.status, grant.anchor_bytes) == ("settled", 5 * GIB)
    assert (grant.free_before, grant.paid_before) == (0, 12 * GIB)
    assert (grant.free_after, grant.paid_after) == (10 * GIB, 12 * GIB)
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 5 * GIB + 22 * GIB
    # Повтор после восстановления не выдаёт пакет второй раз.
    assert (await billing.retry_payment(session, payment.id, None, panel)).already_applied
    assert await _ledger_count(session, user.id, "free_grant") == 2


async def test_several_renewals_and_purchase_during_outage_apply_in_order(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(50))
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(40))
    _, bought = await _buy(session, user, panel, 25, now=_ago(35))
    assert bought.applied and bought.whitelist_pending
    await _pay(session, user, panel, days=180, amount=850, now=_ago(30))
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)

    panel.read_fail_server_ids.clear()
    assert await whitelist.reconcile_usage(session, panel) == 1
    account = await _account(session, user)
    # Расход 5 — до первого продления: 2 + 3 из купленного; затем пакеты и покупка.
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 37 * GIB)
    events = await _events(session, user)
    assert [e.status for e in events][-3:] == ["settled"] * 3
    assert [e.anchor_bytes for e in events][-3:] == [5 * GIB] * 3
    assert await _ledger_count(session, user.id, "free_grant") == 3
    assert await _ledger_count(session, user.id, "purchase") == 1
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 5 * GIB + 47 * GIB


async def test_purchase_during_outage_is_exact_when_balance_covers_usage(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.read_fail_server_ids.add(wl_server.id)
    await _buy(session, user, panel, 25, now=_ago(30))
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(20))  # после покупки
    panel.read_fail_server_ids.clear()
    await whitelist.user_overview(session, user.id, panel)
    account = await _account(session, user)
    # Порядок покупки и расхода не влияет на итог, пока остатка хватает.
    assert (account.free_bytes, account.paid_bytes) == (0, 37 * GIB)
    assert await whitelist.list_open_events(session, user.id) == []


async def test_stale_batch_reading_cannot_anchor_later_payment(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    stale = await panel.read_quota_client(wl_server, EMAIL)  # пакетное чтение на T−45
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(40))
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(30))
    # Чтение начато до события: его нулевой расход не делает событие точным.
    assert await whitelist._reconcile_one(
        session, user.id, stale, _ago(45)
    ) is whitelist.ReconcileOutcome.BUSY
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    assert [e.status for e in await whitelist.list_open_events(session, user.id)] == ["pending"]
    panel.read_fail_server_ids.clear()
    await whitelist.user_overview(session, user.id, panel)
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 12 * GIB)


async def test_restart_after_commit_during_outage_settles_once(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(40))
    payment = await payments.create_request(session, user.id, 175, 30)

    class Interrupted(MockPanelUpdater):
        async def update_expiry(self, *_args):
            raise RuntimeError("process interrupted after durable commit")

    interrupted = Interrupted()
    interrupted.quota_clients = panel.quota_clients
    interrupted.read_fail_server_ids.add(wl_server.id)
    with pytest.raises(RuntimeError):
        await billing.confirm_payment(session, payment.id, None, interrupted, now=_ago(30))
    await session.rollback()
    await session.refresh(payment)
    await session.refresh(user)
    assert payment.status == PaymentStatus.CONFIRMED
    assert [e.free_set for e in await whitelist.list_open_events(session, user.id)] == [
        10 * GIB
    ]

    assert await billing.recover_confirmed_payments(session, panel) == 1
    await session.refresh(payment)
    assert payment.status == PaymentStatus.APPLIED
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (10 * GIB, 12 * GIB)
    assert await _ledger_count(session, user.id, "free_grant") == 2
    assert await whitelist.list_open_events(session, user.id) == []


@pytest.mark.parametrize(
    ("choice", "expected"),
    [("before", (9 * GIB, 22 * GIB)), ("after", (4 * GIB, 25 * GIB))],
)
async def test_unsplittable_usage_stays_uncertain_until_admin_decides(
    session, user, vpn_client, service_on, panel, wl_server, choice, expected
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(30))
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(20))  # после продления?
    panel.read_fail_server_ids.clear()

    overview = await whitelist.user_overview(session, user.id, panel)
    assert overview.uncertain and overview.awaiting
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    events = await whitelist.list_open_events(session, user.id)
    assert [(e.status, e.anchor_min_bytes, e.anchor_max_bytes) for e in events] == [
        ("uncertain", 0, 5 * GIB)
    ]
    assert whitelist.uncertain_outcomes(account, events) == (
        (10 * GIB, 12 * GIB), (5 * GIB, 15 * GIB)
    )
    # Квота — нижняя граница, неразделённый расход не списан произвольно.
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 25 * GIB
    summary = await whitelist.admin_summary(session)
    assert summary.uncertain == 1
    # Следующие события ждут решения, но сохраняют точную привязку.
    _, bought = await _buy(session, user, panel, 10)
    assert bought.applied and bought.whitelist_pending
    later = (await whitelist.list_open_events(session, user.id))[-1]
    assert (later.status, later.anchor_bytes) == ("pending", 5 * GIB)
    panel.consume(wl_server.id, EMAIL, GIB)
    await whitelist.reconcile_usage(session, panel)
    assert (await _account(session, user)).paid_bytes == 15 * GIB
    with pytest.raises(whitelist.WhitelistError):
        await whitelist.adjust_balance(
            session, user.id, free_bytes=None, paid_bytes=GIB, actor_user_id=None,
            reason="x", updater=panel,
        )

    await whitelist.resolve_uncertain(
        session, user.id, choice=choice, actor_user_id=None, reason="проверено", updater=panel
    )
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == expected
    assert account.usage_checkpoint_bytes == 6 * GIB
    assert await whitelist.list_open_events(session, user.id) == []
    assert _wl_state(panel, wl_server).total_bytes == 6 * GIB + sum(expected)
    with pytest.raises(whitelist.WhitelistError):
        await whitelist.resolve_uncertain(
            session, user.id, choice=choice, actor_user_id=None, reason="x", updater=panel
        )


async def test_counter_reset_during_outage_keeps_payment_and_old_balances(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15, used_gb=3)
    panel.read_fail_server_ids.add(wl_server.id)
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(40))
    await _pay(session, user, panel, now=_ago(30))
    panel.reset_traffic(wl_server.id, EMAIL)  # внешний сброс счётчика
    panel.consume(wl_server.id, EMAIL, GIB, at=_ago(20))
    panel.read_fail_server_ids.clear()

    await whitelist.user_overview(session, user.id, panel)
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    assert account.conflict and "сброшен" in account.conflict
    assert await _ledger_count(session, user.id, "usage_rebase") == 1
    events = await whitelist.list_open_events(session, user.id)
    assert [(e.status, e.anchor_min_bytes, e.anchor_max_bytes) for e in events] == [
        ("uncertain", 0, GIB)
    ]
    await whitelist.process_due(session, panel)
    assert _wl_state(panel, wl_server).total_bytes == 25 * GIB  # новая эпоха: 0 + 10 + 15
    await whitelist.resolve_uncertain(
        session, user.id, choice="after", actor_user_id=None, reason="сброс", updater=panel
    )
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (9 * GIB, 15 * GIB)
    assert _wl_state(panel, wl_server).total_bytes == GIB + 24 * GIB


async def test_admin_adjust_requires_reading_and_closes_open_events(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(30))
    with pytest.raises(whitelist.WhitelistError):
        await whitelist.adjust_balance(
            session, user.id, free_bytes=GIB, paid_bytes=GIB, actor_user_id=None,
            reason="x", updater=panel,
        )
    panel.consume(wl_server.id, EMAIL, 5 * GIB, at=_ago(20))
    panel.read_fail_server_ids.clear()
    await whitelist.adjust_balance(
        session, user.id, free_bytes=7 * GIB, paid_bytes=13 * GIB, actor_user_id=None,
        reason="разбор", updater=panel,
    )
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (7 * GIB, 13 * GIB)
    assert account.usage_checkpoint_bytes == 5 * GIB
    assert await whitelist.list_open_events(session, user.id) == []
    assert _wl_state(panel, wl_server).total_bytes == 25 * GIB


async def test_deleted_client_with_unread_usage_leaves_payment_uncertain(
    session, user, vpn_client, service_on, panel, wl_server
):
    from app.services import subscription_delete

    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(30))
    result = await subscription_delete.delete_user_subscription(session, user, panel)
    assert result.deleted
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    events = await whitelist.list_open_events(session, user.id)
    assert [(e.status, e.anchor_max_bytes) for e in events] == [("uncertain", None)]
    with pytest.raises(whitelist.WhitelistError, match="wladjust"):
        await whitelist.resolve_uncertain(
            session, user.id, choice="before", actor_user_id=None, reason="x",
            updater=panel,
        )


async def test_server_replacement_before_reading_does_not_zero_old_usage(
    session, user, vpn_client, service_on, panel, wl_server
):
    await _baseline(session, user, panel, wl_server, 2, 15)
    panel.read_fail_server_ids.add(wl_server.id)
    await _pay(session, user, panel, now=_ago(30))
    wl_server.enabled = False
    await session.commit()
    new = Server(name="WL-2", panel_url="https://wl2.example", username="a", password="b",
                 purpose="whitelist", enabled=True, inventory_status="ready")
    session.add(new)
    await session.flush()
    session.add(ServerInbound(server_id=new.id, inbound_id=3, protocol=Protocol.VLESS))
    await session.commit()
    # Клиент с той же идентичностью уже есть на новой панели.
    panel.quota_clients[(new.id, EMAIL)] = QuotaClientState(
        EMAIL, True, GIB, 1, [3], used_bytes=0, traffic_row_id=500
    )
    await whitelist.user_overview(session, user.id, panel)
    account = await _account(session, user)
    assert (account.free_bytes, account.paid_bytes) == (2 * GIB, 15 * GIB)
    events = await whitelist.list_open_events(session, user.id)
    assert [(e.status, e.anchor_max_bytes) for e in events] == [("uncertain", None)]
